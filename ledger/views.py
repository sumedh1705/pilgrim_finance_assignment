import csv
import logging

from django.db import DatabaseError
from django.db.models import Case, DecimalField, Sum, Value, When
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BankTransaction, InternalLedgerEntry, LedgerEntry, ReconciliationStatus
from .serializers import BankTransactionSerializer, InternalLedgerEntrySerializer, LedgerEntrySerializer
from .services import CSVValidationError, ingest_bank_statement, ingest_internal_ledger, reconcile_transactions, reconciliation_payload

logger = logging.getLogger(__name__)


def dashboard(request):
    return render(request, "dashboard.html")


@method_decorator(csrf_exempt, name="dispatch")
class UploadBankStatementView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "Upload a CSV file using the 'file' form field."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = ingest_bank_statement(uploaded_file)
        except CSVValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class UploadInternalLedgerView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "Upload a CSV file using the 'file' form field."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = ingest_internal_ledger(uploaded_file)
        except CSVValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)


class RunReconciliationView(APIView):
    def get(self, request):
        return self._run()

    def post(self, request):
        return self._run()

    def _run(self):
        try:
            return Response(reconcile_transactions())
        except DatabaseError as exc:
            logger.exception("Reconciliation failed due to database error")
            return Response(
                {
                    "error": "Reconciliation failed due to a database error.",
                    "details": str(exc),
                    "hint": "Ensure Neon DATABASE_URL is set in Vercel and run Django migrations on that database.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SummaryView(APIView):
    def get(self, request):
        bank_totals = BankTransaction.objects.filter(is_duplicate=False).aggregate(
            total_credits=Sum(Case(When(type="credit", then="amount"), default=Value(0), output_field=DecimalField())),
            total_debits=Sum(Case(When(type="debit", then="amount"), default=Value(0), output_field=DecimalField())),
        )
        unmatched_amount = LedgerEntry.objects.filter(reconciliation_status=ReconciliationStatus.UNMATCHED).aggregate(total=Sum("amount"))["total"] or 0
        return Response(
            {
                "total_credits": bank_totals["total_credits"] or 0,
                "total_debits": bank_totals["total_debits"] or 0,
                "unmatched_amount": unmatched_amount,
                "bank_transactions": BankTransaction.objects.filter(is_duplicate=False).count(),
                "internal_entries": InternalLedgerEntry.objects.filter(is_duplicate=False).count(),
                "ledger_entries": LedgerEntry.objects.count(),
            }
        )


class ReconciliationView(APIView):
    def get(self, request):
        payload = reconciliation_payload()
        unmatched_bank = BankTransactionSerializer(payload["unmatched_bank"], many=True).data
        unmatched_internal = InternalLedgerEntrySerializer(payload["unmatched_internal"], many=True).data
        return Response(
            {
                "matched": payload["matched"],
                "unmatched_bank": unmatched_bank,
                "unmatched_internal": unmatched_internal,
                "unmatched": {
                    "bank": unmatched_bank,
                    "internal": unmatched_internal,
                },
            }
        )


class CategoryBreakdownView(APIView):
    def get(self, request):
        rows = (
            BankTransaction.objects.filter(type="debit", is_duplicate=False)
            .values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        return Response(list(rows))


class DailyCashflowView(APIView):
    def get(self, request):
        rows = (
            BankTransaction.objects.filter(is_duplicate=False)
            .values("date")
            .annotate(
                credits=Sum(Case(When(type="credit", then="amount"), default=Value(0), output_field=DecimalField())),
                debits=Sum(Case(When(type="debit", then="amount"), default=Value(0), output_field=DecimalField())),
            )
            .order_by("date")
        )
        return Response(list(rows))


class LedgerExportCSVView(APIView):
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="normalized_ledger.csv"'
        writer = csv.writer(response)
        writer.writerow(["date", "amount", "category", "source", "reconciliation_status"])
        for entry in LedgerEntry.objects.all().order_by("date", "id"):
            writer.writerow([entry.date, entry.amount, entry.category, entry.source, entry.reconciliation_status])
        return response


class BankTransactionListView(APIView):
    def get(self, request):
        return Response(BankTransactionSerializer(BankTransaction.objects.all(), many=True).data)


class InternalLedgerListView(APIView):
    def get(self, request):
        return Response(InternalLedgerEntrySerializer(InternalLedgerEntry.objects.all(), many=True).data)
