"""
The Artificer's Worker — enchanter.py

Polls the jobs table for pending enchantment jobs,
processes them (trivially), writes results back to Postgres.

This is intentionally simple. The worker exists so it can crash.
"""
import hashlib
import logging
import os
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [enchanter] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://workshop:workshop@localhost:5432/workshop"
)

POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "5"))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def process_job(db: Session, job_id: int) -> None:
    # Import here to avoid circular import if models move
    from app.models import Job

    job = db.get(Job, job_id)
    if not job:
        return

    log.info("Processing enchantment job %d", job_id)
    job.status = "processing"
    db.commit()

    # Trivial "enchantment" — the business logic is not the point
    artifact_id = str(uuid.uuid4()).replace("-", "")[:16].upper()
    fingerprint = hashlib.sha256(
        f"{job.commission_id}-{artifact_id}".encode()
    ).hexdigest()[:12]
    report = (
        f"Artifact {artifact_id} bound to commission "
        f"#{job.commission_id}. "
        f"Enchantment seal: {fingerprint}. "
        f"Inscribed at {datetime.now(timezone.utc).isoformat()}."
    )

    job.status = "complete"
    job.artifact_id = artifact_id
    job.report = report
    job.processed_at = datetime.now(timezone.utc)
    db.commit()
    log.info("Job %d complete — artifact %s", job_id, artifact_id)


def run() -> None:
    from app.models import Job

    log.info(
        "Enchanter started. Polling every %ds.", POLL_INTERVAL
    )
    while True:
        try:
            with SessionLocal() as db:
                pending = (
                    db.query(Job)
                    .filter(Job.status == "pending")
                    .order_by(Job.created_at)
                    .all()
                )
                for job in pending:
                    try:
                        process_job(db, job.id)
                    except Exception:
                        log.exception(
                            "Failed processing job %d", job.id
                        )
        except Exception:
            log.exception(
                "DB unavailable, retrying in %ds", POLL_INTERVAL
            )
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
