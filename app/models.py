"""Data model.

Site      – a workplace with a GPS geofence (centre + radius in metres)
Employee  – an hourly-paid worker
TimeEntry – one shift: clock-in time and site, clock-out time (null while working)
"""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class Site(db.Model):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    radius_m: Mapped[float] = mapped_column(Float, default=150.0)


class Employee(db.Model):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # Money as Numeric, never float: 0.1 + 0.2 != 0.3 in floating point.
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(8, 2))

    entries: Mapped[list["TimeEntry"]] = relationship(back_populates="employee")


class TimeEntry(db.Model):
    __tablename__ = "time_entries"
    __table_args__ = (
        # Timesheet queries filter by employee and date range.
        Index("ix_time_entries_employee_clock_in", "employee_id", "clock_in"),
        # At most one open shift per employee, enforced by the database.
        # (Partial unique index: works on Postgres and SQLite.)
        Index(
            "uq_one_open_shift",
            "employee_id",
            unique=True,
            postgresql_where=text("clock_out IS NULL"),
            sqlite_where=text("clock_out IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"))
    clock_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    clock_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="entries")
    site: Mapped[Site] = relationship()

    @property
    def hours(self) -> float | None:
        if self.clock_out is None:
            return None
        start, end = _aware(self.clock_in), _aware(self.clock_out)
        return round((end - start).total_seconds() / 3600, 2)


def _aware(dt: datetime) -> datetime:
    # SQLite drops tzinfo; treat naive values as UTC.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
