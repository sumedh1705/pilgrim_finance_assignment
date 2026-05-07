from io import StringIO

from django.test import TestCase

from .models import BankTransaction, InternalLedgerEntry, LedgerEntry, ReconciliationMatch, ReconciliationStatus
from .services import ingest_bank_statement, ingest_internal_ledger, reconcile_transactions


class FinanceAutomationTests(TestCase):
    def test_ingestion_auto_categorizes_and_skips_duplicate_bank_rows(self):
        csv_file = StringIO(
            "date,narration,amount,type\n"
            "2026-05-02,Swiggy Order Koramangala,850.00,debit\n"
            "2026-05-02,Swiggy Order Koramangala,850.00,debit\n"
        )

        result = ingest_bank_statement(csv_file)

        self.assertEqual(result["created"], 1)
        self.assertEqual(result["duplicates"], 1)
        transaction = BankTransaction.objects.get()
        self.assertEqual(transaction.category, "Food")

    def test_reconciliation_matches_by_amount_date_window_and_similarity(self):
        ingest_bank_statement(
            StringIO(
                "date,narration,amount,type\n"
                "2026-05-02,Swiggy Order Koramangala,850.00,debit\n"
                "2026-05-06,Unknown ATM Withdrawal,5000.00,debit\n"
            )
        )
        ingest_internal_ledger(
            StringIO(
                "date,description,amount,category\n"
                "2026-05-03,Swiggy food order,850.00,Food\n"
                "2026-05-09,ATM cash withdrawal,5000.00,Cash\n"
            )
        )

        result = reconcile_transactions()

        self.assertEqual(result["matched"], 1)
        self.assertEqual(ReconciliationMatch.objects.count(), 1)
        self.assertEqual(LedgerEntry.objects.filter(reconciliation_status=ReconciliationStatus.MATCHED).count(), 2)
        self.assertEqual(LedgerEntry.objects.filter(reconciliation_status=ReconciliationStatus.UNMATCHED).count(), 2)

    def test_internal_ledger_ingestion_uses_provided_category(self):
        result = ingest_internal_ledger(StringIO("date,description,amount,category\n2026-05-01,May salary payroll,120000.00,Income\n"))

        self.assertEqual(result["created"], 1)
        self.assertEqual(InternalLedgerEntry.objects.get().category, "Income")
