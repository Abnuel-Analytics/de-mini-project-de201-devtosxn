"""
Name: jaffle_gen.py
Description: Loads the jafgen-generated Jaffle Shop CSVs into the `raw` schema
    of a local Postgres database, one table per file.
Author: Tosin Ayodele
Update date: 2026-09-05

Usage:
    cd py-project
    uv run jafgen 3                 # writes jaffle-data/
    uv run python -m src.jaffle_gen
"""

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# Connection details come from the environment so no credentials are committed.
DB_USER = os.environ.get("JAFFLE_DB_USER", "postgres")
DB_PASS = os.environ.get("JAFFLE_DB_PASSWORD", "")
DB_HOST = os.environ.get("JAFFLE_DB_HOST", "localhost")
DB_PORT = os.environ.get("JAFFLE_DB_PORT", "5432")
DB_NAME = os.environ.get("JAFFLE_DB_NAME", "jaffle")
SCHEMA_NAME = "raw"

# Anchored on this file so the script runs from any working directory.
ROOT = Path(__file__).resolve().parent.parent / "jaffle-data"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)


def load_jaffle_data():
    """
    Loads every CSV in the jaffle-data directory into the `raw` schema.

    Each file becomes a table named after it, so raw_orders.csv lands in
    raw.raw_orders. Existing tables are replaced, which makes reruns
    idempotent but drops any keys or constraints added by hand.

    Returns:
        bool: True once every file has been loaded, False if there were none.
    """
    print(f"Checking and creating schema '{SCHEMA_NAME}' if missing...")
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};"))
        # SQLAlchemy 2.x does not autocommit, so the schema needs this.
        conn.commit()

    csv_files = sorted(ROOT.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in '{ROOT}'. Please check your path.")
        return False

    for csv_file in csv_files:
        table_name = csv_file.stem
        print(f"Loading {csv_file.name} into {SCHEMA_NAME}.{table_name}...")

        data = pd.read_csv(csv_file)
        data.to_sql(
            name=table_name,
            con=engine,
            schema=SCHEMA_NAME,
            if_exists="replace",
            index=False,
        )
        print(f"Successfully loaded {len(data)} rows into {table_name}.")

    return True


if __name__ == "__main__":
    if load_jaffle_data():
        print("\nAll data successfully migrated to PostgreSQL!")
