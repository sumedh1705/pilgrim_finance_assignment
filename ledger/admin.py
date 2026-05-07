from django.contrib import admin

from .models import BankTransaction, InternalLedgerEntry, LedgerEntry, ReconciliationMatch


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "type", "amount", "category", "is_duplicate", "narration")
    list_filter = ("type", "category", "is_duplicate")
    search_fields = ("narration",)


@admin.register(InternalLedgerEntry)
class InternalLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "amount", "category", "is_duplicate", "description")
    list_filter = ("category", "is_duplicate")
    search_fields = ("description",)


@admin.register(ReconciliationMatch)
class ReconciliationMatchAdmin(admin.ModelAdmin):
    list_display = ("bank_transaction", "internal_entry", "similarity_score", "date_difference_days", "created_at")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "source", "amount", "category", "reconciliation_status")
    list_filter = ("source", "category", "reconciliation_status")
