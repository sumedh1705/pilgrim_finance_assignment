from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BankTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("narration", models.TextField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("type", models.CharField(choices=[("credit", "Credit"), ("debit", "Debit")], max_length=10)),
                ("category", models.CharField(blank=True, max_length=80)),
                ("row_hash", models.CharField(max_length=64, unique=True)),
                ("is_duplicate", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-date", "-id"]},
        ),
        migrations.CreateModel(
            name="InternalLedgerEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("description", models.TextField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("category", models.CharField(blank=True, max_length=80)),
                ("row_hash", models.CharField(max_length=64, unique=True)),
                ("is_duplicate", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-date", "-id"]},
        ),
        migrations.CreateModel(
            name="LedgerEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("category", models.CharField(max_length=80)),
                ("source", models.CharField(choices=[("bank", "Bank"), ("internal", "Internal")], max_length=10)),
                ("reconciliation_status", models.CharField(choices=[("matched", "Matched"), ("unmatched", "Unmatched")], default="unmatched", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("bank_transaction", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="ledger_entry", to="ledger.banktransaction")),
                ("internal_entry", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="ledger_entry", to="ledger.internalledgerentry")),
            ],
            options={"ordering": ["-date", "-id"]},
        ),
        migrations.CreateModel(
            name="ReconciliationMatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("similarity_score", models.FloatField()),
                ("date_difference_days", models.PositiveSmallIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("bank_transaction", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="reconciliation", to="ledger.banktransaction")),
                ("internal_entry", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="reconciliation", to="ledger.internalledgerentry")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
