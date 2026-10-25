from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "sales.csv"
REJECTED_FILE = ROOT / "data" / "rejected_sales.csv"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "order_id", "order_date", "customer_id", "product", "quantity", "unit_price"
]


def get_connection():
    load_dotenv(ROOT / ".env")
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "sales_db"),
        user=os.getenv("DB_USER", "sales_user"),
        password=os.getenv("DB_PASSWORD", "local_demo_password"),
    )


def extract(path: Path) -> pd.DataFrame:
    logger.info("Extracting source data from %s", path)
    df = pd.read_csv(path)
    missing = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"Source file is missing required columns: {missing}")
    logger.info("Extracted %s rows", len(df))
    return df[REQUIRED_COLUMNS].copy()


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    original_count = len(df)
    df = df.copy()

    # Normalize text fields and parse data types.
    for col in ["order_id", "customer_id", "product"]:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace("", pd.NA)

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce").dt.date
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # Reject incomplete rows, invalid dates, non-integer/non-positive quantity,
    # and negative prices.
    invalid = (
        df[["order_id", "order_date", "customer_id", "product",
            "quantity", "unit_price"]].isna().any(axis=1)
        | (df["quantity"] <= 0)
        | (df["quantity"] % 1 != 0)
        | (df["unit_price"] < 0)
    )
    rejected = df.loc[invalid].copy()
    clean = df.loc[~invalid].copy()

    # If duplicate order IDs occur, keep the last valid source occurrence.
    duplicate_mask = clean.duplicated(subset=["order_id"], keep="last")
    rejected_duplicates = clean.loc[duplicate_mask].copy()
    if not rejected_duplicates.empty:
        rejected_duplicates["reject_reason"] = "duplicate order_id"
        rejected = pd.concat([rejected, rejected_duplicates], ignore_index=True)
    clean = clean.loc[~duplicate_mask].copy()

    if "reject_reason" not in rejected.columns:
        rejected["reject_reason"] = "missing or invalid required field"

    clean["quantity"] = clean["quantity"].astype(int)
    clean["unit_price"] = clean["unit_price"].round(2)
    clean["total_amount"] = (clean["quantity"] * clean["unit_price"]).round(2)

    logger.info(
        "Transformed %s source rows: %s clean, %s rejected",
        original_count, len(clean), len(rejected)
    )
    return clean, rejected


def load_to_postgres(df: pd.DataFrame) -> int:
    if df.empty:
        logger.warning("No valid rows to load")
        return 0

    schema_path = ROOT / "sql" / "schema.sql"
    rows = [
        (
            row.order_id, row.order_date, row.customer_id, row.product,
            int(row.quantity), float(row.unit_price), float(row.total_amount)
        )
        for row in df.itertuples(index=False)
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_path.read_text(encoding="utf-8"))
            execute_values(
                cur,
                """
                INSERT INTO sales
                    (order_id, order_date, customer_id, product,
                     quantity, unit_price, total_amount)
                VALUES %s
                ON CONFLICT (order_id) DO UPDATE SET
                    order_date = EXCLUDED.order_date,
                    customer_id = EXCLUDED.customer_id,
                    product = EXCLUDED.product,
                    quantity = EXCLUDED.quantity,
                    unit_price = EXCLUDED.unit_price,
                    total_amount = EXCLUDED.total_amount,
                    loaded_at = NOW()
                """,
                rows,
            )
    logger.info("Loaded/upserted %s rows into PostgreSQL", len(rows))
    return len(rows)


def main() -> None:
    try:
        source = extract(DATA_FILE)
        clean, rejected = transform(source)

        if not rejected.empty:
            rejected.to_csv(REJECTED_FILE, index=False)
            logger.warning("Rejected rows saved to %s", REJECTED_FILE)
        elif REJECTED_FILE.exists():
            REJECTED_FILE.unlink()

        loaded_count = load_to_postgres(clean)
        logger.info(
            "Pipeline completed successfully | source=%s | loaded=%s | rejected=%s",
            len(source), loaded_count, len(rejected)
        )
    except Exception:
        logger.exception("Pipeline failed")
        raise


if __name__ == "__main__":
    main()
