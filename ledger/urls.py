from django.urls import path

from .views import (
    BankTransactionListView,
    CategoryBreakdownView,
    DailyCashflowView,
    InternalLedgerListView,
    LedgerExportCSVView,
    ReconciliationView,
    RunReconciliationView,
    SummaryView,
    UploadBankStatementView,
    UploadInternalLedgerView,
)

urlpatterns = [
    path("upload/bank-statement/", UploadBankStatementView.as_view(), name="upload-bank-statement"),
    path("upload/internal-ledger/", UploadInternalLedgerView.as_view(), name="upload-internal-ledger"),
    path("run-reconciliation/", RunReconciliationView.as_view(), name="run-reconciliation"),
    path("summary/", SummaryView.as_view(), name="summary"),
    path("reconciliation/", ReconciliationView.as_view(), name="reconciliation"),
    path("category-breakdown/", CategoryBreakdownView.as_view(), name="category-breakdown"),
    path("daily-cashflow/", DailyCashflowView.as_view(), name="daily-cashflow"),
    path("export/ledger.csv", LedgerExportCSVView.as_view(), name="ledger-export-csv"),
    path("bank-transactions/", BankTransactionListView.as_view(), name="bank-transactions"),
    path("internal-ledger/", InternalLedgerListView.as_view(), name="internal-ledger"),
]
