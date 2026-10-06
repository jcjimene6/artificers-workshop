from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, DateTime, ForeignKey, Integer
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Commission(Base):
    __tablename__ = "commissions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    patron: Mapped[str] = mapped_column(String(120))
    discipline: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(30), default="submitted"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc,
    )

    notes: Mapped[list["Note"]] = relationship(
        back_populates="commission",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="commission",
        cascade="all, delete-orphan",
    )


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    commission_id: Mapped[int] = mapped_column(
        ForeignKey("commissions.id"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )

    commission: Mapped["Commission"] = relationship(
        back_populates="notes"
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    commission_id: Mapped[int] = mapped_column(
        ForeignKey("commissions.id"), index=True
    )
    # pending -> processing -> complete / failed
    status: Mapped[str] = mapped_column(
        String(30), default="pending"
    )
    artifact_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    report: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    commission: Mapped["Commission"] = relationship(
        back_populates="jobs"
    )
