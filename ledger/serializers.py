from rest_framework import serializers

from .models import BankTransaction, InternalLedgerEntry, LedgerEntry


class BankTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransaction
        fields = ["id", "date", "narration", "amount", "type", "category", "is_duplicate"]


class InternalLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = InternalLedgerEntry
        fields = ["id", "date", "description", "amount", "category", "is_duplicate"]


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ["id", "date", "amount", "category", "source", "reconciliation_status"]
