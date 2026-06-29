# Finance Data Automation & Dashboard

## Objective

I built a mini finance automation system using Django + Python that:

- Processes raw financial data
- Performs reconciliation
- Stores structured ledger entries
- Exposes insights via APIs
- Visualizes data in a simple dashboard

## Problem Statement

I worked with two CSV files:

1. `bank_statement.csv`  
   Fields: `date`, `narration`, `amount`, `type` (`credit`/`debit`)
2. `internal_ledger.csv`  
   Fields: `date`, `description`, `amount`, `category`

## Tasks Implemented

### 1) Data Ingestion

- Uploaded both CSVs via API endpoints.
- Stored incoming rows in PostgreSQL-backed Django models.
- Validated required columns, dates, and amounts during ingestion.

### 2) Reconciliation Logic

Matched transactions between bank statements and internal ledger rows using:

- Exact amount match
- Date difference <= 2 days
- Fuzzy narration/description similarity

Output generated:

- Matched transactions
- Unmatched transactions from bank side
- Unmatched transactions from internal side

### 3) Ledger Automation

Generated a normalized ledger table containing:

- `date`
- `amount`
- `category`
- `source` (`bank` / `internal`)
- `reconciliation_status` (`matched` / `unmatched`)

### 4) APIs (Django REST)

Exposed these required APIs:

- `/summary` -> total credits, total debits, unmatched amount
- `/reconciliation` -> matched and unmatched entries
- `/category-breakdown` -> expense grouped by category

I also added supporting endpoints:

- `/run-reconciliation` (GET/POST)
- `/daily-cashflow`
- `/export/ledger.csv`

### 5) Dashboard

I built a clean Django template dashboard that includes:

- Expense by category
- Daily cashflow trend
- Reconciliation status

## Implemented

- Auto-categorization rules (example: `Swiggy` -> `Food`)
- Background reconciliation trigger via cron-compatible command
- Duplicate row handling using row hashes

## Deployment

- Backend hosted on Vercel with Neon PostgreSQL
- Live URL: [https://finance-data-automation.vercel.app/](https://finance-data-automation.vercel.app/)
- GitHub repo: [https://github.com/sumedh1705/Finance-Data-Automation-Dashboard](https://github.com/sumedh1705/Finance-Data-Automation-Dashboard)
- Sample CSVs used: `sample_data/bank_statement.csv`, `sample_data/internal_ledger.csv`
