import csv
import io
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from . import cache
from .extensions import db
from .geo import inside_geofence
from .models import Employee, Site, TimeEntry, utcnow
from .schemas import ClockInIn, ClockOutIn, EmployeeIn, PeriodQuery, SiteIn

bp = Blueprint("api", __name__)


@bp.errorhandler(ValidationError)
def bad_request(err):
    return jsonify(error="invalid request", details=err.errors(include_url=False, include_context=False)), 400


def _json(model):
    return model.model_validate(request.get_json(silent=True) or {})


def _period():
    q = PeriodQuery.model_validate(request.args.to_dict())
    start = datetime.combine(q.start, time.min, tzinfo=timezone.utc)
    end = datetime.combine(q.end + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return q, start, end


def _entry_json(e: TimeEntry):
    return {
        "id": e.id,
        "employee_id": e.employee_id,
        "site_id": e.site_id,
        "clock_in": e.clock_in.isoformat(),
        "clock_out": e.clock_out.isoformat() if e.clock_out else None,
        "hours": e.hours,
    }


# ---- Sites and employees -------------------------------------------------

@bp.post("/sites")
def create_site():
    data = _json(SiteIn)
    site = Site(**data.model_dump())
    db.session.add(site)
    db.session.commit()
    return jsonify(id=site.id, **data.model_dump()), 201


@bp.post("/employees")
def create_employee():
    data = _json(EmployeeIn)
    emp = Employee(**data.model_dump())
    db.session.add(emp)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="email already exists"), 409
    return jsonify(id=emp.id, name=emp.name, email=emp.email, hourly_rate=str(emp.hourly_rate)), 201


# ---- Clocking ------------------------------------------------------------

@bp.post("/clock-in")
def clock_in():
    data = _json(ClockInIn)
    emp = db.get_or_404(Employee, data.employee_id)
    site = db.get_or_404(Site, data.site_id)

    if not inside_geofence(data.latitude, data.longitude, site):
        return jsonify(error="outside site geofence"), 422

    entry = TimeEntry(employee_id=emp.id, site_id=site.id, clock_in=utcnow())
    db.session.add(entry)
    try:
        db.session.commit()
    except IntegrityError:
        # The partial unique index rejected a second open shift.
        db.session.rollback()
        return jsonify(error="already clocked in"), 409

    cache.invalidate_employee(emp.id)
    return jsonify(_entry_json(entry)), 201


@bp.post("/clock-out")
def clock_out():
    data = _json(ClockOutIn)
    entry = db.session.scalar(
        select(TimeEntry)
        .where(TimeEntry.employee_id == data.employee_id, TimeEntry.clock_out.is_(None))
        .with_for_update()  # lock the row so two clock-outs can't race (Postgres)
    )
    if entry is None:
        return jsonify(error="no open shift"), 409
    if not inside_geofence(data.latitude, data.longitude, entry.site):
        return jsonify(error="outside site geofence"), 422

    entry.clock_out = utcnow()
    db.session.commit()
    cache.invalidate_employee(data.employee_id)
    return jsonify(_entry_json(entry))


# ---- Timesheets and payroll ----------------------------------------------

@bp.get("/employees/<int:employee_id>/timesheet")
def timesheet(employee_id):
    q, start, end = _period()
    key = cache.timesheet_key(employee_id, q.start, q.end)

    cached = cache.get_cached(key)
    if cached is not None:
        return jsonify(cached), 200, {"X-Cache": "HIT"}

    db.get_or_404(Employee, employee_id)
    entries = db.session.scalars(
        select(TimeEntry)
        .where(TimeEntry.employee_id == employee_id,
               TimeEntry.clock_in >= start, TimeEntry.clock_in < end)
        .order_by(TimeEntry.clock_in)
    ).all()
    body = {
        "employee_id": employee_id,
        "start": q.start.isoformat(),
        "end": q.end.isoformat(),
        "entries": [_entry_json(e) for e in entries],
        "total_hours": round(sum(e.hours or 0 for e in entries), 2),
    }
    cache.set_cached(key, body)
    return jsonify(body), 200, {"X-Cache": "MISS"}


@bp.get("/payroll/export")
def payroll_export():
    """CSV of completed hours and gross pay per employee for a period."""
    q, start, end = _period()
    rows = db.session.execute(
        select(Employee, TimeEntry)
        .join(TimeEntry, TimeEntry.employee_id == Employee.id)
        .where(TimeEntry.clock_in >= start, TimeEntry.clock_in < end,
               TimeEntry.clock_out.is_not(None))
        .order_by(Employee.id)
    ).all()

    totals = {}
    for emp, entry in rows:
        hours, _ = totals.get(emp.id, (Decimal("0"), emp))
        totals[emp.id] = (hours + Decimal(str(entry.hours)), emp)

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["employee_id", "name", "email", "hours", "hourly_rate", "gross_pay"])
    for emp_id, (hours, emp) in totals.items():
        pay = (hours * emp.hourly_rate).quantize(Decimal("0.01"))
        w.writerow([emp_id, emp.name, emp.email, hours, emp.hourly_rate, pay])

    filename = f"payroll_{q.start}_{q.end}.csv"
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})
