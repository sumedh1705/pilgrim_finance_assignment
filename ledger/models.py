import hashlib

from django.db import models


class ReconciliationStatus(models.TextChoices):
    MATCHED = "matched", "Matched"
    UNMATCHED = "unmatched", "Unmatched"


class Source(models.TextChoices):
    BANK = "bank", "Bank"
    INTERNAL = "internal", "Internal"


class BankTransaction(models.Model):
    date = models.DateField()
    narration = models.TextField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    type = models.CharField(max_length=10, choices=[("credit", "Credit"), ("debit", "Debit")])
    category = models.CharField(max_length=80, blank=True)
    row_hash = models.CharField(max_length=64, unique=True)
    is_duplicate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.type} {self.amount} {self.narration[:40]}"


class InternalLedgerEntry(models.Model):
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    category = models.CharField(max_length=80, blank=True)
    row_hash = models.CharField(max_length=64, unique=True)
    is_duplicate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.amount} {self.description[:40]}"


class ReconciliationMatch(models.Model):
    bank_transaction = models.OneToOneField(BankTransaction, on_delete=models.CASCADE, related_name="reconciliation")
    internal_entry = models.OneToOneField(InternalLedgerEntry, on_delete=models.CASCADE, related_name="reconciliation")
    similarity_score = models.FloatField()
    date_difference_days = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.bank_transaction_id} <-> {self.internal_entry_id} ({self.similarity_score:.2f})"


class LedgerEntry(models.Model):
    date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    category = models.CharField(max_length=80)
    source = models.CharField(max_length=10, choices=Source.choices)
    reconciliation_status = models.CharField(
        max_length=12,
        choices=ReconciliationStatus.choices,
        default=ReconciliationStatus.UNMATCHED,
    )
    bank_transaction = models.OneToOneField(
        BankTransaction,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="ledger_entry",
    )
    internal_entry = models.OneToOneField(
        InternalLedgerEntry,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="ledger_entry",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.source} {self.amount} {self.reconciliation_status}"


def make_row_hash(*values):
    normalized = "|".join(str(value).strip().lower() for value in values)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
