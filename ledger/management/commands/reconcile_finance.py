from django.core.management.base import BaseCommand

from ledger.services import reconcile_transactions


class Command(BaseCommand):
    help = "Run transaction reconciliation and rebuild the normalized ledger."

    def handle(self, *args, **options):
        result = reconcile_transactions()
        self.stdout.write(
            self.style.SUCCESS(
                "Reconciliation complete: "
                f"{result['matched']} matched, "
                f"{result['unmatched_bank']} unmatched bank, "
                f"{result['unmatched_internal']} unmatched internal."
            )
        )
