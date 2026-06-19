import uuid
from datetime import date, datetime, time, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from src.turso_database import BASE_DIR, TursoConnection


load_dotenv(BASE_DIR / ".env")


FIELD_MAP = {
    "tracking_id": "TrackingId",
    "university_job_id": "UniversityJobId",
    "job_id": "JobId",
    "job_title": "JobTitle",
    "portal_name": "PortalName",
    "university": "University",
    "country": "Country",
    "posting_status": "PostingStatus",
    "applicants_count": "ApplicantsCount",
    "last_applicants_count": "LastApplicantsCount",
    "new_applicants_count": "NewApplicantsCount",
    "submitted_date": "SubmittedDate",
    "submitted_time": "SubmittedTime",
}

TRACKING_COLUMNS = list(FIELD_MAP.keys())

LEGACY_TRACKING_COLUMNS = {
    "portal_display_name",
    "submitted_at",
    "posted_at",
    "last_checked_at",
    "created_at",
    "updated_at",
    "portal_posting_id",
    "proof_link",
    "notes",
    "last_run_id",
    "batch_id",
}


class TrackingManager:
    """Stores application tracking data in Turso/libSQL."""

    _schema_ready = False

    def __init__(self, database_url: str | None = None):
        if not TursoConnection.is_configured():
            raise ValueError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set in .env")

        if not TrackingManager._schema_ready:
            self.ensure_schema()
            TrackingManager._schema_ready = True

    @staticmethod
    def is_configured() -> bool:
        return TursoConnection.is_configured()

    def ensure_schema(self):
        self._ensure_tracking_table()
        statements = [
            """
            CREATE INDEX IF NOT EXISTS idx_application_tracking_job_id
            ON application_tracking (job_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_application_tracking_portal_name
            ON application_tracking (portal_name)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_application_tracking_status
            ON application_tracking (posting_status)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_application_tracking_submitted
            ON application_tracking (submitted_date, submitted_time)
            """,
        ]

        for statement in statements:
            TursoConnection.execute(statement)
        TursoConnection.commit()

    def record_application_posting(
        self,
        job_id: str,
        job_title: str,
        portal_name: str,
        portal_display_name: str = "",
        country: str = "",
        university_job_id: str = "",
        posting_status: str = "POSTED",
        applicants_count: int = 0,
        submitted_at: str | datetime = None,
        portal_posting_id: str = None,
        proof_link: str = None,
        notes: str = None,
        run_id: str = None,
        batch_id: str = None,
        posted_at: str | datetime = None,
    ) -> Dict[str, Any]:
        applicant_total = self._safe_int(applicants_count)
        submitted_timestamp = (
            self._parse_timestamp(submitted_at)
            or self._parse_timestamp(posted_at)
            or datetime.now(timezone.utc).replace(microsecond=0)
        )

        tracking_id = f"TRACK_{uuid.uuid4().hex[:10].upper()}"
        TursoConnection.execute("""
            INSERT INTO application_tracking (
                tracking_id,
                university_job_id,
                job_id,
                job_title,
                portal_name,
                university,
                country,
                posting_status,
                applicants_count,
                last_applicants_count,
                new_applicants_count,
                submitted_date,
                submitted_time
            )
            VALUES (
                :tracking_id,
                :university_job_id,
                :job_id,
                :job_title,
                :portal_name,
                :university,
                :country,
                :posting_status,
                :applicants_count,
                :last_applicants_count,
                :new_applicants_count,
                :submitted_date,
                :submitted_time
            )
        """, {
            "tracking_id": tracking_id,
            "university_job_id": str(university_job_id or portal_posting_id or ""),
            "job_id": str(job_id),
            "job_title": str(job_title or job_id),
            "portal_name": str(portal_name).strip().lower(),
            "university": str(portal_display_name or portal_name),
            "country": str(country or ""),
            "posting_status": self._status(posting_status),
            "applicants_count": applicant_total,
            "last_applicants_count": 0,
            "new_applicants_count": applicant_total,
            "submitted_date": self._format_date_value(submitted_timestamp),
            "submitted_time": self._format_time_value(submitted_timestamp),
        })
        TursoConnection.commit()

        return self.get_tracking_record(tracking_id)

    def get_application_tracking(
        self,
        job_id: str = None,
        portal_name: str = None,
        status: str = None,
    ) -> List[Dict[str, Any]]:
        filters = []
        params = []

        if job_id:
            filters.append("job_id = ?")
            params.append(str(job_id))
        if portal_name:
            filters.append("portal_name = ?")
            params.append(str(portal_name).lower())
        if status:
            filters.append("posting_status = ?")
            params.append(self._status(status))

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = TursoConnection.fetch_all(f"""
            SELECT *
            FROM application_tracking
            {where_clause}
            ORDER BY
                submitted_date IS NULL,
                submitted_date DESC,
                submitted_time DESC,
                tracking_id DESC
        """, tuple(params))

        return [self._row_to_record(row) for row in rows]

    def get_tracking_record(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        row = TursoConnection.fetch_one("""
            SELECT *
            FROM application_tracking
            WHERE tracking_id = ?
        """, (tracking_id,))

        return self._row_to_record(row) if row else None

    def update_applicant_count(
        self,
        applicants_count: int,
        tracking_id: str = None,
        job_id: str = None,
        portal_name: str = None,
        notes: str = None,
        status: str = None,
    ) -> Dict[str, Any]:
        applicant_total = self._safe_int(applicants_count)
        if applicant_total < 0:
            raise ValueError("Applicants count cannot be negative")

        if not tracking_id and not (job_id and portal_name):
            raise ValueError("Provide tracking_id or both job_id and portal_name")

        if tracking_id:
            current = TursoConnection.fetch_one("""
                SELECT *
                FROM application_tracking
                WHERE tracking_id = ?
            """, (tracking_id,))
        else:
            current = TursoConnection.fetch_one("""
                SELECT *
                FROM application_tracking
                WHERE job_id = ? AND portal_name = ?
                ORDER BY submitted_date DESC, submitted_time DESC, tracking_id DESC
                LIMIT 1
            """, (str(job_id), str(portal_name).lower()))

        if not current:
            raise ValueError("Tracking record not found")

        previous_total = self._safe_int(current["applicants_count"])
        TursoConnection.execute("""
            UPDATE application_tracking
            SET last_applicants_count = :last_applicants_count,
                applicants_count = :applicants_count,
                new_applicants_count = :new_applicants_count,
                posting_status = COALESCE(:posting_status, posting_status)
            WHERE tracking_id = :tracking_id
        """, {
            "tracking_id": current["tracking_id"],
            "last_applicants_count": previous_total,
            "applicants_count": applicant_total,
            "new_applicants_count": max(applicant_total - previous_total, 0),
            "posting_status": self._status(status) if status else None,
        })
        TursoConnection.commit()

        return self.get_tracking_record(current["tracking_id"])

    def get_tracking_summary(self) -> Dict[str, Any]:
        totals = TursoConnection.fetch_one("""
            SELECT
                COUNT(*) AS total_postings,
                COALESCE(SUM(applicants_count), 0) AS total_applicants,
                COUNT(DISTINCT job_id) AS jobs_tracked,
                COUNT(DISTINCT portal_name) AS portals_tracked
            FROM application_tracking
        """) or {}

        by_status = TursoConnection.fetch_all("""
            SELECT posting_status AS PostingStatus, COUNT(*) AS postings
            FROM application_tracking
            GROUP BY posting_status
            ORDER BY postings DESC
        """)

        by_job = TursoConnection.fetch_all("""
            SELECT
                job_id AS JobId,
                job_title AS JobTitle,
                COUNT(*) AS postings,
                COALESCE(SUM(applicants_count), 0) AS applicants
            FROM application_tracking
            GROUP BY job_id, job_title
            ORDER BY applicants DESC, postings DESC
        """)

        by_portal = TursoConnection.fetch_all("""
            SELECT
                portal_name AS PortalName,
                university AS University,
                COUNT(*) AS postings,
                COALESCE(SUM(applicants_count), 0) AS applicants
            FROM application_tracking
            GROUP BY portal_name, university
            ORDER BY applicants DESC, postings DESC
        """)

        return {
            "total_postings": self._safe_int(totals.get("total_postings")),
            "total_applicants": self._safe_int(totals.get("total_applicants")),
            "jobs_tracked": self._safe_int(totals.get("jobs_tracked")),
            "portals_tracked": self._safe_int(totals.get("portals_tracked")),
            "by_status": [self._clean_record(dict(row)) for row in by_status],
            "by_job": [self._clean_record(dict(row)) for row in by_job],
            "by_portal": [self._clean_record(dict(row)) for row in by_portal],
        }

    def _ensure_tracking_table(self):
        table = TursoConnection.fetch_one("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'application_tracking'
        """)

        if not table:
            TursoConnection.execute(self._create_table_sql("application_tracking"))
            return

        existing_columns = self._table_columns("application_tracking")
        target_columns = set(TRACKING_COLUMNS)
        needs_rebuild = (
            bool(target_columns - existing_columns)
            or bool(existing_columns & LEGACY_TRACKING_COLUMNS)
            or bool(existing_columns - target_columns)
        )
        if needs_rebuild:
            self._rebuild_tracking_table(existing_columns)

    def _rebuild_tracking_table(self, existing_columns: set[str]):
        temp_table = "application_tracking_migrated"
        TursoConnection.execute(f"DROP TABLE IF EXISTS {temp_table}")
        TursoConnection.execute(self._create_table_sql(temp_table))

        insert_columns = ", ".join(TRACKING_COLUMNS)
        select_expressions = ", ".join(
            self._migration_expression(column, existing_columns)
            for column in TRACKING_COLUMNS
        )
        TursoConnection.execute(f"""
            INSERT INTO {temp_table} ({insert_columns})
            SELECT {select_expressions}
            FROM application_tracking
        """)
        TursoConnection.execute("DROP TABLE application_tracking")
        TursoConnection.execute(f"ALTER TABLE {temp_table} RENAME TO application_tracking")

    @staticmethod
    def _create_table_sql(table_name: str) -> str:
        return f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                tracking_id TEXT PRIMARY KEY,
                university_job_id TEXT,
                job_id TEXT NOT NULL,
                job_title TEXT,
                portal_name TEXT,
                university TEXT,
                country TEXT,
                posting_status TEXT DEFAULT 'POSTED',
                applicants_count INTEGER DEFAULT 0,
                last_applicants_count INTEGER DEFAULT 0,
                new_applicants_count INTEGER DEFAULT 0,
                submitted_date TEXT,
                submitted_time TEXT
            )
        """

    @staticmethod
    def _table_columns(table_name: str) -> set[str]:
        rows = TursoConnection.fetch_all(f"PRAGMA table_info({table_name})")
        return {str(row["name"]) for row in rows}

    def _migration_expression(self, column: str, existing_columns: set[str]) -> str:
        source_timestamp = self._source_timestamp_expression(existing_columns)
        portal_name_expr = self._coalesce(existing_columns, ["portal_name"], "''")
        posting_status_expr = self._coalesce(existing_columns, ["posting_status"], "'POSTED'")

        expressions = {
            "tracking_id": self._coalesce(
                existing_columns,
                ["tracking_id"],
                "'TRACK_' || upper(substr(hex(randomblob(8)), 1, 10))",
            ),
            "university_job_id": self._coalesce(
                existing_columns,
                ["university_job_id", "portal_posting_id"],
                "''",
            ),
            "job_id": self._coalesce(existing_columns, ["job_id"], "''"),
            "job_title": self._coalesce(existing_columns, ["job_title", "job_id"], "''"),
            "portal_name": f"lower({portal_name_expr})",
            "university": self._coalesce(
                existing_columns,
                ["university", "portal_display_name", "portal_name"],
                "''",
            ),
            "country": self._coalesce(existing_columns, ["country"], "''"),
            "posting_status": f"upper({posting_status_expr})",
            "applicants_count": self._coalesce(existing_columns, ["applicants_count"], "0"),
            "last_applicants_count": self._coalesce(existing_columns, ["last_applicants_count"], "0"),
            "new_applicants_count": self._coalesce(existing_columns, ["new_applicants_count"], "0"),
            "submitted_date": self._submitted_part_expression(
                "submitted_date",
                "date",
                source_timestamp,
                existing_columns,
            ),
            "submitted_time": self._submitted_part_expression(
                "submitted_time",
                "time",
                source_timestamp,
                existing_columns,
            ),
        }
        return expressions[column]

    @staticmethod
    def _source_timestamp_expression(existing_columns: set[str]) -> str | None:
        timestamp_columns = [
            column
            for column in ["submitted_at", "posted_at", "created_at", "updated_at"]
            if column in existing_columns
        ]
        if not timestamp_columns:
            return None
        expressions = [f"NULLIF({column}, '')" for column in timestamp_columns]
        if len(expressions) == 1:
            return expressions[0]
        return "COALESCE(" + ", ".join(expressions) + ")"

    @staticmethod
    def _submitted_part_expression(
        column: str,
        sql_function: str,
        source_timestamp: str | None,
        existing_columns: set[str],
    ) -> str:
        if column in existing_columns and source_timestamp:
            return f"COALESCE(NULLIF({column}, ''), {sql_function}({source_timestamp}))"
        if column in existing_columns:
            return f"NULLIF({column}, '')"
        if source_timestamp:
            return f"{sql_function}({source_timestamp})"
        return "NULL"

    @staticmethod
    def _coalesce(existing_columns: set[str], candidates: List[str], default: str) -> str:
        expressions = [
            f"NULLIF({column}, '')"
            for column in candidates
            if column in existing_columns
        ]
        expressions.append(default)
        if len(expressions) == 1:
            return expressions[0]
        return "COALESCE(" + ", ".join(expressions) + ")"

    @staticmethod
    def _status(value: str | None) -> str:
        return str(value or "POSTED").upper()

    @staticmethod
    def _safe_int(value: Any) -> int:
        if value is None or value == "":
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_timestamp(value: str | datetime = None) -> Optional[datetime]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, date):
            parsed = datetime.combine(value, time.min)
        else:
            text = str(value).strip()
            if not text:
                return None
            try:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError:
                try:
                    parsed = datetime.combine(date.fromisoformat(text), time.min)
                except ValueError:
                    return None

        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc)
        return parsed.replace(microsecond=0)

    @classmethod
    def _format_date_value(cls, value: Any) -> Optional[str]:
        parsed = cls._parse_timestamp(value)
        if parsed:
            return parsed.strftime("%Y-%m-%d")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        text = str(value).strip() if value is not None else ""
        return text or None

    @classmethod
    def _format_time_value(cls, value: Any) -> Optional[str]:
        if isinstance(value, time):
            return value.strftime("%H:%M:%S")
        parsed = cls._parse_timestamp(value)
        if parsed:
            return parsed.strftime("%H:%M:%S")
        text = str(value).strip() if value is not None else ""
        try:
            return time.fromisoformat(text).strftime("%H:%M:%S") if text else None
        except ValueError:
            return text or None

    def _row_to_record(self, row) -> Dict[str, Any]:
        record = {}
        for key, value in dict(row).items():
            record[FIELD_MAP.get(key, key)] = value
        return self._clean_record(record)

    @staticmethod
    def _clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}
        for key, value in record.items():
            if isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, (date, time)):
                cleaned[key] = value.isoformat()
            elif value is None:
                cleaned[key] = None
            elif isinstance(value, str) and value.strip() == "":
                cleaned[key] = None
            else:
                cleaned[key] = value
        return cleaned
