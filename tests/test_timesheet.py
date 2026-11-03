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
