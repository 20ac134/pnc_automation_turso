import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import libsql
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class TursoConnection:
    """Small sqlite/libSQL wrapper used by the data managers."""

    _conn = None
    _lock = threading.RLock()
    _named_param_pattern = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")

    @classmethod
    def is_configured(cls) -> bool:
        return bool(os.getenv("TURSO_DATABASE_URL") and os.getenv("TURSO_AUTH_TOKEN"))

    @classmethod
    def get(cls):
        database_url = os.getenv("TURSO_DATABASE_URL")
        auth_token = os.getenv("TURSO_AUTH_TOKEN")
        if not database_url:
            raise ValueError("TURSO_DATABASE_URL is not set in .env")
        if not auth_token:
            raise ValueError("TURSO_AUTH_TOKEN is not set in .env")

        with cls._lock:
            if cls._conn is None:
                cls._conn = libsql.connect(database=database_url, auth_token=auth_token)
            return cls._conn

    @classmethod
    def execute(cls, query: str, params: Optional[Iterable[Any] | Dict[str, Any]] = None):
        with cls._lock:
            conn = cls.get()
            prepared_query, prepared_params = cls._prepare(query, params)
            return conn.execute(prepared_query, prepared_params)

    @classmethod
    def executemany(cls, query: str, rows: Iterable[Iterable[Any]]):
        with cls._lock:
            conn = cls.get()
            cursor = conn.cursor()
            cursor.executemany(query, rows)
            conn.commit()

    @classmethod
    def commit(cls):
        with cls._lock:
            cls.get().commit()

    @classmethod
    def fetch_all(cls, query: str, params: Optional[Iterable[Any] | Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with cls._lock:
            cursor = cls.execute(query, params)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description or []]
        return [dict(zip(columns, row)) for row in rows]

    @classmethod
    def fetch_one(cls, query: str, params: Optional[Iterable[Any] | Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        with cls._lock:
            cursor = cls.execute(query, params)
            row = cursor.fetchone()
            columns = [column[0] for column in cursor.description or []]
        return dict(zip(columns, row)) if row else None

    @classmethod
    def scalar(cls, query: str, params: Optional[Iterable[Any] | Dict[str, Any]] = None):
        with cls._lock:
            cursor = cls.execute(query, params)
            row = cursor.fetchone()
        return row[0] if row else None

    @classmethod
    def _prepare(cls, query: str, params: Optional[Iterable[Any] | Dict[str, Any]]):
        if not params:
            return query, ()
        if not isinstance(params, dict):
            return query, params

        values = []

        def replace(match):
            name = match.group(1)
            if name not in params:
                raise ValueError(f"Missing SQL parameter: {name}")
            values.append(params[name])
            return "?"

        return cls._named_param_pattern.sub(replace, query), tuple(values)
