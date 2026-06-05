"""
Copy the old Supabase/Postgres tables into Turso.

Usage:
  1. Keep TURSO_DATABASE_URL and TURSO_AUTH_TOKEN in .env.
  2. Add one old Supabase/Postgres URL variable to .env:
       OLD_DATABASE_URL=postgresql://...
     or
       SUPABASE_DATABASE_URL=postgresql://...
     or temporarily keep
       DATABASE_URL=postgresql://...
  3. Run:
       python scripts/migrate_supabase_to_turso.py
"""

import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

from src.turso_data_manager import TursoDataManager
from src.tracking_manager import TrackingManager
from src.turso_database import TursoConnection


TABLES = [
    ("job_posts", "job_id"),
    ("posting_runs", "run_id"),
    ("job_templates", "template_id"),
    ("portal_urls", "portal_key"),
    ("application_tracking", "tracking_id"),
]


def get_old_database_url() -> str:
    database_url = (
        os.getenv("OLD_DATABASE_URL")
        or os.getenv("SUPABASE_DATABASE_URL")
        or os.getenv("DATABASE_URL")
    )
    if not database_url:
        raise RuntimeError(
            "Add OLD_DATABASE_URL, SUPABASE_DATABASE_URL, or DATABASE_URL to .env "
            "with the old Supabase/Postgres connection string."
        )
    return database_url


def connect_postgres(database_url: str):
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required only for this one-time migration. "
            "Install it with: pip install \"psycopg[binary]\""
        ) from exc

    return psycopg.connect(database_url, row_factory=dict_row)


def clean_value(value: Any):
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: clean_value(value) for key, value in row.items()}


def upsert(table: str, pk: str, row: Dict[str, Any]):
    clean = clean_row(row)
    columns = list(clean.keys())
    updates = [column for column in columns if column != pk]
    if not columns:
        return

    TursoConnection.execute(f"""
        INSERT INTO {table} ({", ".join(columns)})
        VALUES ({", ".join(":" + column for column in columns)})
        ON CONFLICT ({pk}) DO UPDATE SET
            {", ".join(f"{column} = excluded.{column}" for column in updates)}
    """, clean)


def table_rows(pg_conn, table: str) -> Iterable[Dict[str, Any]]:
    with pg_conn.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table}")
        yield from cursor.fetchall()


def migrate():
    TursoDataManager()
    TrackingManager()

    old_database_url = get_old_database_url()
    totals = {}
    with connect_postgres(old_database_url) as pg_conn:
        for table, pk in TABLES:
            count = 0
            for row in table_rows(pg_conn, table):
                upsert(table, pk, dict(row))
                count += 1
            TursoConnection.commit()
            totals[table] = count

    return totals


if __name__ == "__main__":
    totals = migrate()
    print("Migration complete:")
    for table, count in totals.items():
        print(f"  {table}: {count}")
