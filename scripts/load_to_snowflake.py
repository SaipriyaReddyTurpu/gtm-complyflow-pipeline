"""
Load synthetic ComplyFlow CSVs into Snowflake RAW tables.

Connects to Snowflake using account credentials, then loads each CSV
in /data into its matching table in GTM_DB.RAW, in dependency order.
"""

import snowflake.connector
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

import os
from dotenv import load_dotenv

load_dotenv()

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")


TABLE_LOAD_ORDER = [
    "sales_reps",
    "accounts",
    "leads",
    "opportunities",
    "subscriptions",
    "revenue_events",
    "customer_health_scores",
    "retention_experiments",
]


def get_connection():
    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
    )

import pandas as pd
from snowflake.connector.pandas_tools import write_pandas


def load_table(conn, table_name):
    csv_path = DATA_DIR / f"{table_name}.csv"
    df = pd.read_csv(csv_path)

    df.columns = [c.upper() for c in df.columns]

    success, nchunks, nrows, _ = write_pandas(
        conn,
        df,
        table_name=table_name.upper(),
    )

    if success:
        print(f"loaded {nrows:>6} rows -> {table_name}")
    else:
        print(f"FAILED to load {table_name}")


def main():
    print("Connecting to Snowflake...")
    conn = get_connection()
    print("Connected.\n")

    try:
        for table_name in TABLE_LOAD_ORDER:
            load_table(conn, table_name)
    finally:
        conn.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()