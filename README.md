# Advanced Sales Data Engineering Pipeline

A portfolio-ready batch ETL project using **Python, Pandas, PostgreSQL, SQL, Docker, logging, and data-quality checks**.

## Architecture

`data/sales.csv` → Python extract → validate/clean/transform → PostgreSQL staging table → PostgreSQL analytics table → SQL reporting queries

### What it demonstrates
- Reading CSV data and handling missing/invalid values
- Deduplication using `order_id`
- Data validation and rejected-row reporting
- Transformations such as `total_amount = quantity * unit_price`
- Loading into PostgreSQL with an upsert (`ON CONFLICT`)
- Run logging and row-count summaries
- SQL analytics for revenue, product performance, and monthly trends
- Reproducible local environment with Docker Compose

> This is a learning/portfolio project. Use synthetic data, and do not describe it as production experience unless you have actually operated it in production.

## Prerequisites
- Python 3.10+
- Docker Desktop (recommended) or a locally installed PostgreSQL server

## 1. Start PostgreSQL

From this project directory:

```bash
docker compose up -d
```

PostgreSQL will be available at `localhost:5432`. The demo credentials are defined in `docker-compose.yml`; change them before using this outside a local learning environment.

## 2. Create a virtual environment and install dependencies

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configure the connection

Copy `.env.example` to `.env` and update values if needed.

Windows:
```powershell
copy .env.example .env
```

macOS/Linux:
```bash
cp .env.example .env
```

## 4. Run the pipeline

```bash
python src/pipeline.py
```

Expected behavior:
- Creates the database tables if needed
- Reads `data/sales.csv`
- Validates and transforms records
- Writes invalid rows to `data/rejected_sales.csv` when any are found
- Upserts clean records into PostgreSQL
- Prints a summary and writes logs to `logs/pipeline.log`

## 5. Run analytics SQL

Open `sql/analytics.sql` in a PostgreSQL client such as `psql`, pgAdmin, or DBeaver and execute the queries.

Example using `psql` inside the container:

```bash
docker exec -i sales-postgres psql -U sales_user -d sales_db < sql/analytics.sql
```

## Suggested interview explanation

"I built a batch sales data pipeline using Python and PostgreSQL. It extracts sales records from CSV, validates required fields and numeric values, removes duplicate order IDs, derives total sales, and loads records into PostgreSQL using an upsert to support reruns. I added logging, rejected-row output, database constraints, and SQL analytics for revenue trends and product performance."

Only claim the features you have run and verified yourself.

## Repository structure

```text
advanced-sales-data-pipeline/
├── data/
│   └── sales.csv
├── logs/                  # created at runtime
├── sql/
│   ├── schema.sql
│   └── analytics.sql
├── src/
│   └── pipeline.py
├── .env.example
├── .gitignore
├── docker-compose.yml
└── requirements.txt
```

## Next upgrades
1. Add automated tests with `pytest`.
2. Schedule daily runs with cron or Windows Task Scheduler.
3. Add incremental extraction using a source watermark.
4. Add Airflow orchestration.
5. Add a cloud storage/data warehouse destination (for example, S3 + Redshift or Azure Data Lake + Synapse).
