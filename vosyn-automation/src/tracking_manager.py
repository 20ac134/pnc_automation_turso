import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from src.turso_database import BASE_DIR, TursoConnection


load_dotenv(BASE_DIR / ".env")


FIELD_MAP = {
    "tracking_id": "TrackingId",
    "job_id": "JobId",
    "job_title": "JobTitle",
    "portal_name": "PortalName",
    "portal_display_name": "PortalDisplayName",
    "portal_posting_id": "PortalPostingId",
    "posting_status": "PostingStatus",
    "applicants_count": "ApplicantsCount",
    "last_applicants_count": "LastApplicantsCount",
    "new_applicants_count": "NewApplicantsCount",
    "posted_at": "PostedAt",
    "last_checked_at": "LastCheckedAt",
    "proof_link": "ProofLink",
    "notes": "Notes",
    "last_run_id": "LastRunId",
    "batch_id": "BatchId",
    "created_at": "CreatedAt",
    "updated_at": "UpdatedAt",
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
        statements = [
            """
            CREATE TABLE IF NOT EXISTS application_tracking (
                tracking_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                job_title TEXT,
                portal_name TEXT,
                portal_display_name TEXT,
                portal_posting_id TEXT,
                posting_status TEXT DEFAULT 'POSTED',
                applicants_count INTEGER DEFAULT 0,
                last_applicants_count INTEGER DEFAULT 0,
                new_applicants_count INTEGER DEFAULT 0,
                posted_at TEXT,
                last_checked_at TEXT,
                proof_link TEXT,
                notes TEXT,
                last_run_id TEXT,
                batch_id TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """,
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
        portal_posting_id: str = None,
        proof_link: str = None,
        posting_status: str = "POSTED",
        applicants_count: int = 0,
        notes: str = None,
        run_id: str = None,
        batch_id: str = None,
        posted_at: str | datetime = None,
    ) -> Dict[str, Any]:
        now = self._now()
        applicant_total = self._safe_int(applicants_count)
        posted_timestamp = self._parse_timestamp(posted_at) or now
        last_checked = now if applicant_total > 0 else None

        if run_id:
            existing = TursoConnection.fetch_one("""
                SELECT *
                FROM application_tracking
                WHERE last_run_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (run_id,))

            if existing:
                TursoConnection.execute("""
                    UPDATE application_tracking
                    SET posting_status = :posting_status,
                        portal_posting_id = COALESCE(:portal_posting_id, portal_posting_id),
                        proof_link = COALESCE(:proof_link, proof_link),
                        notes = COALESCE(:notes, notes),
                        updated_at = :updated_at
                    WHERE tracking_id = :tracking_id
                """, {
                    "tracking_id": existing["tracking_id"],
                    "posting_status": self._status(posting_status),
                    "portal_posting_id": portal_posting_id,
                    "proof_link": proof_link,
                    "notes": notes,
                    "updated_at": now,
                })
                TursoConnection.commit()
                return self.get_tracking_record(existing["tracking_id"])

        tracking_id = f"TRACK_{uuid.uuid4().hex[:10].upper()}"
        TursoConnection.execute("""
            INSERT INTO application_tracking (
                tracking_id,
                job_id,
                job_title,
                portal_name,
                portal_display_name,
                portal_posting_id,
                posting_status,
                applicants_count,
                last_applicants_count,
                new_applicants_count,
                posted_at,
                last_checked_at,
                proof_link,
                notes,
                last_run_id,
                batch_id,
                created_at,
                updated_at
            )
            VALUES (
                :tracking_id,
                :job_id,
                :job_title,
                :portal_name,
                :portal_display_name,
                :portal_posting_id,
                :posting_status,
                :applicants_count,
                :last_applicants_count,
                :new_applicants_count,
                :posted_at,
                :last_checked_at,
                :proof_link,
                :notes,
                :last_run_id,
                :batch_id,
                :created_at,
                :updated_at
            )
        """, {
            "tracking_id": tracking_id,
            "job_id": str(job_id),
            "job_title": str(job_title or job_id),
            "portal_name": str(portal_name).strip().lower(),
            "portal_display_name": str(portal_display_name or portal_name),
            "portal_posting_id": portal_posting_id,
            "posting_status": self._status(posting_status),
            "applicants_count": applicant_total,
            "last_applicants_count": 0,
            "new_applicants_count": applicant_total,
            "posted_at": posted_timestamp,
            "last_checked_at": last_checked,
            "proof_link": proof_link,
            "notes": notes,
            "last_run_id": run_id,
            "batch_id": batch_id,
            "created_at": now,
            "updated_at": now,
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
            ORDER BY posted_at IS NULL, posted_at DESC, created_at DESC
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
                ORDER BY created_at DESC
                LIMIT 1
            """, (str(job_id), str(portal_name).lower()))

        if not current:
            raise ValueError("Tracking record not found")

        previous_total = self._safe_int(current["applicants_count"])
        now = self._now()
        TursoConnection.execute("""
            UPDATE application_tracking
            SET last_applicants_count = :last_applicants_count,
                applicants_count = :applicants_count,
                new_applicants_count = :new_applicants_count,
                last_checked_at = :last_checked_at,
                updated_at = :updated_at,
                notes = COALESCE(:notes, notes),
                posting_status = COALESCE(:posting_status, posting_status)
            WHERE tracking_id = :tracking_id
        """, {
            "tracking_id": current["tracking_id"],
            "last_applicants_count": previous_total,
            "applicants_count": applicant_total,
            "new_applicants_count": max(applicant_total - previous_total, 0),
            "last_checked_at": now,
            "updated_at": now,
            "notes": notes,
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
                portal_display_name AS PortalDisplayName,
                COUNT(*) AS postings,
                COALESCE(SUM(applicants_count), 0) AS applicants
            FROM application_tracking
            GROUP BY portal_name, portal_display_name
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

    @staticmethod
    def _status(value: str | None) -> str:
        return str(value or "POSTED").upper()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _safe_int(value: Any) -> int:
        if value is None or value == "":
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_timestamp(value: str | datetime = None) -> Optional[str]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            parsed = value
        else:
            try:
                parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.replace(microsecond=0).isoformat()

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
            else:
                cleaned[key] = value
        return cleaned
