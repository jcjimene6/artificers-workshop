import os
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db, engine
from app import models, schemas

# Create tables if running without Alembic (dev convenience)
# In production the init container runs `alembic upgrade head`
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="The Artificer's Workshop")

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


# ---------------------------------------------------------------------------
# Workshop — commission list
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def workshop(request: Request, db: Session = Depends(get_db)):
    commissions = (
        db.query(models.Commission)
        .order_by(models.Commission.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "workshop.html",
        {"request": request, "commissions": commissions},
    )


# ---------------------------------------------------------------------------
# Create commission (form POST)
# ---------------------------------------------------------------------------

@app.post("/commissions")
def create_commission(
    patron: str = Form(...),
    discipline: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    data = schemas.CommissionCreate(
        patron=patron,
        discipline=discipline,
        title=title,
        description=description,
    )
    commission = models.Commission(**data.model_dump())
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return RedirectResponse(
        url=f"/commissions/{commission.id}", status_code=303
    )


# ---------------------------------------------------------------------------
# Commission detail
# ---------------------------------------------------------------------------

@app.get("/commissions/{commission_id}", response_class=HTMLResponse)
def commission_detail(
    commission_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    commission = db.get(models.Commission, commission_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Not found")
    return templates.TemplateResponse(
        "commission.html",
        {
            "request": request,
            "commission": commission,
            "valid_statuses": schemas.VALID_STATUSES,
            "valid_disciplines": schemas.VALID_DISCIPLINES,
        },
    )


# ---------------------------------------------------------------------------
# Update status
# ---------------------------------------------------------------------------

@app.post("/commissions/{commission_id}/status")
def update_status(
    commission_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    commission = db.get(models.Commission, commission_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Not found")

    data = schemas.CommissionStatusUpdate(status=status)
    commission.status = data.status
    commission.updated_at = datetime.now(timezone.utc)

    # When marked complete, enqueue an enchantment job
    if data.status == "complete":
        job = models.Job(commission_id=commission.id)
        db.add(job)

    db.commit()
    return RedirectResponse(
        url=f"/commissions/{commission_id}", status_code=303
    )


# ---------------------------------------------------------------------------
# Add note
# ---------------------------------------------------------------------------

@app.post("/commissions/{commission_id}/notes")
def add_note(
    commission_id: int,
    body: str = Form(...),
    db: Session = Depends(get_db),
):
    commission = db.get(models.Commission, commission_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Not found")
    note = models.Note(commission_id=commission_id, body=body)
    db.add(note)
    db.commit()
    return RedirectResponse(
        url=f"/commissions/{commission_id}", status_code=303
    )


# ---------------------------------------------------------------------------
# Scrying Chamber — health dashboard
# ---------------------------------------------------------------------------

@app.get("/scrying", response_class=HTMLResponse)
def scrying_chamber(
    request: Request,
    db: Session = Depends(get_db),
):
    # Archive (Postgres) health
    try:
        db.execute(text("SELECT 1"))
        archive_status = "healthy"
    except Exception:
        archive_status = "unreachable"

    # Queue depth — pending enchantment jobs
    pending_jobs = (
        db.query(models.Job)
        .filter(models.Job.status == "pending")
        .count()
    )

    # Last successful enchantment
    last_job = (
        db.query(models.Job)
        .filter(models.Job.status == "complete")
        .order_by(models.Job.processed_at.desc())
        .first()
    )

    return templates.TemplateResponse(
        "scrying.html",
        {
            "request": request,
            "archive_status": archive_status,
            "pending_jobs": pending_jobs,
            "last_job": last_job,
            "now": datetime.now(timezone.utc),
        },
    )
