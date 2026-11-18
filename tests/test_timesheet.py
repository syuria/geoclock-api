import csv
import io
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.extensions import db
from app.models import TimeEntry


def add_shift(employee_id, site_id, start, hours):
    db.session.add(TimeEntry(employee_id=employee_id, site_id=site_id,
                             clock_in=start, clock_out=start + timedelta(hours=hours)))
    db.session.commit()


MON = datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc)
PERIOD = "start=2026-11-02&end=2026-11-08"


def test_timesheet_totals_hours(client, employee, site):
    add_shift(employee["id"], site["id"], MON, 8)
    add_shift(employee["id"], site["id"], MON + timedelta(days=1), 7.5)
    add_shift(employee["id"], site["id"], MON + timedelta(days=10), 4)  # outside period

    r = client.get(f"/api/employees/{employee['id']}/timesheet?{PERIOD}")
    assert r.status_code == 200
    body = r.get_json()
    assert len(body["entries"]) == 2
    assert body["total_hours"] == 15.5


def test_timesheet_is_cached_then_invalidated(client, employee, site):
    url = f"/api/employees/{employee['id']}/timesheet?{PERIOD}"
    assert client.get(url).headers["X-Cache"] == "MISS"
    assert client.get(url).headers["X-Cache"] == "HIT"

    # A clock-in must clear the cached timesheet so hours are never stale.
    from conftest import ON_SITE
    client.post("/api/clock-in", json={"employee_id": employee["id"], "site_id": site["id"], **ON_SITE})
    assert client.get(url).headers["X-Cache"] == "MISS"


def test_bad_period_is_400(client, employee):
    r = client.get(f"/api/employees/{employee['id']}/timesheet?start=nope&end=2026-11-08")
    assert r.status_code == 400


def test_payroll_export_csv(client, employee, site):
    add_shift(employee["id"], site["id"], MON, 8)
    add_shift(employee["id"], site["id"], MON + timedelta(days=1), 7.5)

    r = client.get(f"/api/payroll/export?{PERIOD}")
    assert r.status_code == 200
    assert r.mimetype == "text/csv"
    rows = list(csv.DictReader(io.StringIO(r.get_data(as_text=True))))
    assert len(rows) == 1
    assert Decimal(rows[0]["hours"]) == Decimal("15.5")
    assert rows[0]["gross_pay"] == "193.75"  # 15.5 h x £12.50

WEEK2 = "start=2026-11-02&end=2026-11-15"   # two full weeks, Mon 2 Nov to Sun 15 Nov


def test_overtime_over_40_hours_in_a_week(client, employee, site):
    # Five 9-hour shifts, Monday to Friday = 45 hours in one week
    for day in range(5):
        add_shift(employee["id"], site["id"], MON + timedelta(days=day), 9)

    r = client.get(f"/api/payroll/export?{WEEK2}")
    row = list(csv.DictReader(io.StringIO(r.get_data(as_text=True))))[0]
    assert Decimal(row["hours"]) == Decimal("45")
    assert Decimal(row["regular_hours"]) == Decimal("40")
    assert Decimal(row["overtime_hours"]) == Decimal("5")
    assert row["gross_pay"] == "593.75"   # 40 x 12.50 + 5 x 12.50 x 1.5


def test_overtime_is_counted_per_week_not_per_period(client, employee, site):
    # 30 hours in each of two weeks = 60 hours total, but no single week over 40
    for week in range(2):
        for day in range(4):
            add_shift(employee["id"], site["id"], MON + timedelta(weeks=week, days=day), 7.5)

    r = client.get(f"/api/payroll/export?{WEEK2}")
    row = list(csv.DictReader(io.StringIO(r.get_data(as_text=True))))[0]
    assert Decimal(row["overtime_hours"]) == Decimal("0")
    assert row["gross_pay"] == "750.00"   # 60 x 12.50