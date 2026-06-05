import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from src.turso_database import TursoConnection


JOB_COLUMNS = [
    "JobId", "Title", "Description", "Requirements", "Location", "City",
    "Province", "JobType", "Industry", "JobFunction", "StudentGroup",
    "Department", "Salary", "HourlyRate", "StartDate", "ApplicationDeadline",
    "Status", "CreatedAt", "StartedAt", "FinishedAt", "LockedBy",
]

RUN_COLUMNS = [
    "RunId", "JobId", "PortalName", "RunStatus", "PortalPostingId",
    "ProofLink", "ErrorReason", "Attempts", "CreatedAt", "StartedAt",
    "FinishedAt",
]

TEMPLATE_COLUMNS = [
    "TemplateId", "TemplateName", "DefaultTitle", "DeaultDescription",
    "DefaultLocation",
]

PORTAL_COLUMNS = ["#", "PortalKey", "UniversityName", "Country", "URL", "Platform"]


JOB_DB_TO_API = {
    "job_id": "JobId",
    "title": "Title",
    "description": "Description",
    "requirements": "Requirements",
    "location": "Location",
    "city": "City",
    "province": "Province",
    "job_type": "JobType",
    "industry": "Industry",
    "job_function": "JobFunction",
    "student_group": "StudentGroup",
    "department": "Department",
    "salary": "Salary",
    "hourly_rate": "HourlyRate",
    "start_date": "StartDate",
    "application_deadline": "ApplicationDeadline",
    "status": "Status",
    "created_at": "CreatedAt",
    "started_at": "StartedAt",
    "finished_at": "FinishedAt",
    "locked_by": "LockedBy",
}

RUN_DB_TO_API = {
    "run_id": "RunId",
    "job_id": "JobId",
    "portal_name": "PortalName",
    "run_status": "RunStatus",
    "portal_posting_id": "PortalPostingId",
    "proof_link": "ProofLink",
    "error_reason": "ErrorReason",
    "attempts": "Attempts",
    "created_at": "CreatedAt",
    "started_at": "StartedAt",
    "finished_at": "FinishedAt",
}

TEMPLATE_DB_TO_API = {
    "template_id": "TemplateId",
    "template_name": "TemplateName",
    "default_title": "DefaultTitle",
    "default_description": "DeaultDescription",
    "default_location": "DefaultLocation",
}

PORTAL_DB_TO_API = {
    "number": "#",
    "portal_key": "PortalKey",
    "university_name": "UniversityName",
    "country": "Country",
    "url": "URL",
    "platform": "Platform",
}


class TursoDataManager:
    """Stores core automation data in Turso/libSQL."""

    _schema_ready = False

    def __init__(self, database_url: str | None = None):
        if not TursoConnection.is_configured():
            raise ValueError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set in .env")

        if not TursoDataManager._schema_ready:
            self.ensure_schema()
            TursoDataManager._schema_ready = True

    @staticmethod
    def is_configured() -> bool:
        return TursoConnection.is_configured()

    def ensure_schema(self):
        statements = [
            """
            CREATE TABLE IF NOT EXISTS job_posts (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                requirements TEXT,
                location TEXT,
                city TEXT,
                province TEXT,
                job_type TEXT,
                industry TEXT,
                job_function TEXT,
                student_group TEXT,
                department TEXT,
                salary TEXT,
                hourly_rate TEXT,
                start_date TEXT,
                application_deadline TEXT,
                status TEXT DEFAULT 'QUEUED',
                created_at TEXT,
                started_at TEXT,
                finished_at TEXT,
                locked_by TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS posting_runs (
                run_id TEXT PRIMARY KEY,
                job_id TEXT,
                portal_name TEXT,
                run_status TEXT DEFAULT 'QUEUED',
                portal_posting_id TEXT,
                proof_link TEXT,
                error_reason TEXT,
                attempts INTEGER DEFAULT 0,
                created_at TEXT,
                started_at TEXT,
                finished_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS job_templates (
                template_id TEXT PRIMARY KEY,
                template_name TEXT,
                default_title TEXT,
                default_description TEXT,
                default_location TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS portal_urls (
                portal_key TEXT PRIMARY KEY,
                number INTEGER,
                university_name TEXT,
                country TEXT,
                url TEXT,
                platform TEXT
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_job_posts_status ON job_posts(status)",
            "CREATE INDEX IF NOT EXISTS idx_posting_runs_job_id ON posting_runs(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_posting_runs_status ON posting_runs(run_status)",
            "CREATE INDEX IF NOT EXISTS idx_portal_urls_country ON portal_urls(country)",
        ]

        for statement in statements:
            TursoConnection.execute(statement)
        TursoConnection.commit()

    def read_sheet(self, sheet: str) -> pd.DataFrame:
        if sheet == "JobPosts":
            return self.get_job_posts_df()
        if sheet == "PostingRuns":
            return self.get_posting_runs_df()
        if sheet == "JobTemplates":
            return self.get_job_templates_df()
        raise ValueError(f"Unsupported sheet: {sheet}")

    def get_job_posts_df(self) -> pd.DataFrame:
        rows = TursoConnection.fetch_all("""
            SELECT *
            FROM job_posts
            ORDER BY job_id
        """)
        return self._records_to_df(rows, JOB_DB_TO_API, JOB_COLUMNS)

    def get_posting_runs_df(self) -> pd.DataFrame:
        rows = TursoConnection.fetch_all("""
            SELECT *
            FROM posting_runs
            ORDER BY run_id
        """)
        return self._records_to_df(rows, RUN_DB_TO_API, RUN_COLUMNS)

    def get_job_templates_df(self) -> pd.DataFrame:
        rows = TursoConnection.fetch_all("""
            SELECT *
            FROM job_templates
            ORDER BY template_id
        """)
        return self._records_to_df(rows, TEMPLATE_DB_TO_API, TEMPLATE_COLUMNS)

    def get_portal_urls_df(self) -> pd.DataFrame:
        rows = TursoConnection.fetch_all("""
            SELECT *
            FROM portal_urls
            ORDER BY number IS NULL, number, portal_key
        """)
        return self._records_to_df(rows, PORTAL_DB_TO_API, PORTAL_COLUMNS)

    def get_portal_url_map(self) -> Dict[str, str]:
        rows = TursoConnection.fetch_all("SELECT portal_key, url FROM portal_urls")
        return {str(row["portal_key"]).strip().lower(): str(row["url"]).strip() for row in rows}

    def get_queued_jobs(self) -> List[Dict[str, Any]]:
        return [
            row
            for row in self.get_job_posts_df().to_dict("records")
            if str(row.get("Status", "")).upper() == "QUEUED"
        ]

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        row = TursoConnection.fetch_one(
            "SELECT * FROM job_posts WHERE job_id = ?",
            (job_id,),
        )
        return self._row_to_api_record(row, JOB_DB_TO_API) if row else None

    def get_posting_runs(self, job_id: str) -> List[Dict[str, Any]]:
        rows = TursoConnection.fetch_all(
            "SELECT * FROM posting_runs WHERE job_id = ? ORDER BY run_id",
            (job_id,),
        )
        return [self._row_to_api_record(row, RUN_DB_TO_API) for row in rows]

    def get_queued_runs(self, job_id: str) -> List[Dict[str, Any]]:
        return [r for r in self.get_posting_runs(job_id) if str(r.get("RunStatus", "")).upper() == "QUEUED"]

    def transition_job_status(
        self,
        job_id: str,
        from_status: str,
        to_status: str,
        locked_by: str = None,
    ) -> bool:
        now = self._now()
        updates = {
            "status": to_status,
            "locked_by": locked_by,
            "started_at": now if to_status == "RUNNING" else None,
            "finished_at": now if to_status in ["POSTED", "FAILED", "PARTIAL_FAILED"] else None,
            "job_id": job_id,
            "from_status": from_status,
        }
        TursoConnection.execute("""
            UPDATE job_posts
            SET status = :status,
                locked_by = COALESCE(:locked_by, locked_by),
                started_at = COALESCE(:started_at, started_at),
                finished_at = COALESCE(:finished_at, finished_at)
            WHERE job_id = :job_id AND status = :from_status
        """, updates)
        changed = TursoConnection.scalar("SELECT changes()")
        TursoConnection.commit()
        return bool(changed)

    def update_posting_run(
        self,
        run_id: str,
        status: str,
        portal_posting_id: str = None,
        proof_link: str = None,
        error_reason: str = None,
    ):
        current_attempts = TursoConnection.scalar(
            "SELECT attempts FROM posting_runs WHERE run_id = ?",
            (run_id,),
        )
        if current_attempts is None:
            print(f"Warning: Run {run_id} not found")
            return

        TursoConnection.execute("""
            UPDATE posting_runs
            SET run_status = :run_status,
                portal_posting_id = COALESCE(:portal_posting_id, portal_posting_id),
                proof_link = COALESCE(:proof_link, proof_link),
                error_reason = COALESCE(:error_reason, error_reason),
                attempts = :attempts,
                finished_at = :finished_at
            WHERE run_id = :run_id
        """, {
            "run_id": run_id,
            "run_status": status,
            "portal_posting_id": portal_posting_id,
            "proof_link": proof_link,
            "error_reason": error_reason,
            "attempts": int(current_attempts or 0) + 1,
            "finished_at": self._now(),
        })
        TursoConnection.commit()

    def transition_run_status(self, run_id: str, from_status: str, to_status: str) -> bool:
        TursoConnection.execute("""
            UPDATE posting_runs
            SET run_status = :to_status,
                started_at = COALESCE(:started_at, started_at)
            WHERE run_id = :run_id AND run_status = :from_status
        """, {
            "run_id": run_id,
            "from_status": from_status,
            "to_status": to_status,
            "started_at": self._now() if to_status == "RUNNING" else None,
        })
        changed = TursoConnection.scalar("SELECT changes()")
        TursoConnection.commit()
        return bool(changed)

    def create_job(
        self,
        title: str,
        description: str,
        location: str,
        portals: List[str],
        salary: str = None,
        template_id: str = None,
    ) -> str:
        job_id = f"JOB_{uuid.uuid4().hex[:8].upper()}"
        now = self._now()
        job_data = {
            "job_id": job_id,
            "title": title,
            "description": description,
            "requirements": None,
            "location": location,
            "city": None,
            "province": None,
            "job_type": None,
            "industry": None,
            "job_function": None,
            "student_group": None,
            "department": None,
            "salary": salary,
            "hourly_rate": None,
            "start_date": None,
            "application_deadline": None,
            "status": "QUEUED",
            "created_at": now,
            "started_at": None,
            "finished_at": None,
            "locked_by": None,
        }

        self._upsert("job_posts", "job_id", job_data)
        for portal in portals:
            run_data = {
                "run_id": f"RUN_{uuid.uuid4().hex[:8].upper()}",
                "job_id": job_id,
                "portal_name": portal,
                "run_status": "QUEUED",
                "portal_posting_id": None,
                "proof_link": None,
                "error_reason": None,
                "attempts": 0,
                "created_at": now,
                "started_at": None,
                "finished_at": None,
            }
            self._upsert("posting_runs", "run_id", run_data)
        TursoConnection.commit()

        print(f"Created job {job_id} with {len(portals)} posting runs")
        return job_id

    def finalize_job_status(self, job_id: str):
        runs = self.get_posting_runs(job_id)
        statuses = [r["RunStatus"] for r in runs]
        if statuses and all(s == "POSTED" for s in statuses):
            return "POSTED"
        if statuses and all(s == "FAILED" for s in statuses):
            return "FAILED"
        return "PARTIAL_FAILED"

    def _upsert(self, table: str, pk: str, data: Dict[str, Any]):
        clean_data = {key: self._to_db_value(value) for key, value in data.items()}
        columns = list(clean_data.keys())
        updates = [col for col in columns if col != pk]
        TursoConnection.execute(f"""
            INSERT INTO {table} ({", ".join(columns)})
            VALUES ({", ".join(":" + col for col in columns)})
            ON CONFLICT ({pk}) DO UPDATE SET
                {", ".join(f"{col} = excluded.{col}" for col in updates)}
        """, clean_data)

    def _records_to_df(self, rows: List[Dict[str, Any]], field_map: Dict[str, str], columns: List[str]) -> pd.DataFrame:
        records = [self._row_to_api_record(row, field_map) for row in rows]
        return pd.DataFrame(records, columns=columns)

    def _row_to_api_record(self, row, field_map: Dict[str, str]) -> Dict[str, Any]:
        return {
            api_key: self._clean_output_value(dict(row).get(db_key))
            for db_key, api_key in field_map.items()
        }

    @staticmethod
    def _clean_output_value(value: Any):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    @staticmethod
    def _to_db_value(value: Any):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
