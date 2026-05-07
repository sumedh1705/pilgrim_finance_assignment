import csv
from datetime import datetime
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

from django.db import IntegrityError, transaction

from .category_rules import categorize
from .models import (
    BankTransaction,
    InternalLedgerEntry,
    LedgerEntry,
    ReconciliationMatch,
    ReconciliationStatus,
    Source,
    make_row_hash,
)

DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y")
SIMILARITY_THRESHOLD = 0.45


class CSVValidationError(ValueError):
    pass


def parse_date(value):
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), date_format).date()
        except ValueError:
            continue
    raise CSVValidationError(f"Invalid date: {value}")


def parse_amount(value):
    try:
        return Decimal(str(value).strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, AttributeError):
        raise CSVValidationError(f"Invalid amount: {value}") from None


def _read_csv(file_obj, required_columns):
    decoded = (line.decode("utf-8-sig") if isinstance(line, bytes) else line for line in file_obj)
    reader = csv.DictReader(decoded)
    if not reader.fieldnames:
        raise CSVValidationError("CSV file is empty or missing a header row.")

    columns = {name.strip().lower() for name in reader.fieldnames}
    missing = set(required_columns) - columns
    if missing:
        raise CSVValidationError(f"Missing required columns: {', '.join(sorted(missing))}")
    return [{(key or "").strip().lower(): value for key, value in row.items()} for row in reader]


def ingest_bank_statement(file_obj):
    rows = _read_csv(file_obj, {"date", "narration", "amount", "type"})
    created = duplicates = 0
    errors = []

    for index, row in enumerate(rows, start=2):
        try:
            date = parse_date(row["date"])
            narration = row["narration"].strip()
            amount = parse_amount(row["amount"])
            txn_type = row["type"].strip().lower()
            if txn_type not in {"credit", "debit"}:
                raise CSVValidationError("type must be either credit or debit")
            row_hash = make_row_hash("bank", date, narration, amount, txn_type)
            _, was_created = BankTransaction.objects.get_or_create(
                row_hash=row_hash,
                defaults={
                    "date": date,
                    "narration": narration,
                    "amount": amount,
                    "type": txn_type,
                    "category": categorize(narration),
                },
            )
            created += int(was_created)
            duplicates += int(not was_created)
        except (CSVValidationError, IntegrityError) as exc:
            errors.append({"row": index, "error": str(exc)})

    return {"created": created, "duplicates": duplicates, "errors": errors}


def ingest_internal_ledger(file_obj):
    rows = _read_csv(file_obj, {"date", "description", "amount", "category"})
    created = duplicates = 0
    errors = []

    for index, row in enumerate(rows, start=2):
        try:
            date = parse_date(row["date"])
            description = row["description"].strip()
            amount = parse_amount(row["amount"])
            category = row.get("category", "").strip() or categorize(description)
            row_hash = make_row_hash("internal", date, description, amount, category)
            _, was_created = InternalLedgerEntry.objects.get_or_create(
                row_hash=row_hash,
                defaults={
                    "date": date,
                    "description": description,
                    "amount": amount,
                    "category": category,
                },
            )
            created += int(was_created)
            duplicates += int(not was_created)
        except (CSVValidationError, IntegrityError) as exc:
            errors.append({"row": index, "error": str(exc)})

    return {"created": created, "duplicates": duplicates, "errors": errors}


def similarity(left, right):
    return SequenceMatcher(None, left.lower().strip(), right.lower().strip()).ratio()


def reconcile_transactions():
    with transaction.atomic():
        ReconciliationMatch.objects.all().delete()

        unmatched_bank = BankTransaction.objects.filter(is_duplicate=False)
        unmatched_internal = InternalLedgerEntry.objects.filter(is_duplicate=False)
        used_internal_ids = set()
        matches = []

        for bank_txn in unmatched_bank.order_by("date", "id"):
            candidates = unmatched_internal.filter(amount=bank_txn.amount).filter(
                date__gte=bank_txn.date - timedelta(days=2),
                date__lte=bank_txn.date + timedelta(days=2),
            ).exclude(id__in=used_internal_ids)

            best_candidate = None
            best_score = 0.0
            for internal_entry in candidates:
                score = similarity(bank_txn.narration, internal_entry.description)
                if score > best_score:
                    best_candidate = internal_entry
                    best_score = score

            if best_candidate and best_score >= SIMILARITY_THRESHOLD:
                used_internal_ids.add(best_candidate.id)
                matches.append(
                    ReconciliationMatch(
                        bank_transaction=bank_txn,
                        internal_entry=best_candidate,
                        similarity_score=round(best_score, 4),
                        date_difference_days=abs((bank_txn.date - best_candidate.date).days),
                    )
                )

        ReconciliationMatch.objects.bulk_create(matches)
        rebuild_normalized_ledger()

    return {
        "matched": len(matches),
        "unmatched_bank": BankTransaction.objects.filter(reconciliation__isnull=True, is_duplicate=False).count(),
        "unmatched_internal": InternalLedgerEntry.objects.filter(reconciliation__isnull=True, is_duplicate=False).count(),
    }


def rebuild_normalized_ledger():
    LedgerEntry.objects.all().delete()
    matched_bank_ids = set(ReconciliationMatch.objects.values_list("bank_transaction_id", flat=True))
    matched_internal_ids = set(ReconciliationMatch.objects.values_list("internal_entry_id", flat=True))

    bank_entries = [
        LedgerEntry(
            date=txn.date,
            amount=txn.amount,
            category=txn.category or categorize(txn.narration),
            source=Source.BANK,
            reconciliation_status=ReconciliationStatus.MATCHED if txn.id in matched_bank_ids else ReconciliationStatus.UNMATCHED,
            bank_transaction=txn,
        )
        for txn in BankTransaction.objects.filter(is_duplicate=False)
    ]
    internal_entries = [
        LedgerEntry(
            date=entry.date,
            amount=entry.amount,
            category=entry.category or categorize(entry.description),
            source=Source.INTERNAL,
            reconciliation_status=ReconciliationStatus.MATCHED if entry.id in matched_internal_ids else ReconciliationStatus.UNMATCHED,
            internal_entry=entry,
        )
        for entry in InternalLedgerEntry.objects.filter(is_duplicate=False)
    ]
    LedgerEntry.objects.bulk_create(bank_entries + internal_entries)


def reconciliation_payload():
    matches = ReconciliationMatch.objects.select_related("bank_transaction", "internal_entry")
    matched = [
        {
            "bank_transaction_id": match.bank_transaction_id,
            "internal_entry_id": match.internal_entry_id,
            "amount": match.bank_transaction.amount,
            "bank_date": match.bank_transaction.date,
            "internal_date": match.internal_entry.date,
            "narration": match.bank_transaction.narration,
            "description": match.internal_entry.description,
            "similarity_score": match.similarity_score,
        }
        for match in matches
    ]

    return {
        "matched": matched,
        "unmatched_bank": BankTransaction.objects.filter(reconciliation__isnull=True, is_duplicate=False),
        "unmatched_internal": InternalLedgerEntry.objects.filter(reconciliation__isnull=True, is_duplicate=False),
    }
