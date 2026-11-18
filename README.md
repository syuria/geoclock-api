# GeoClock

A time-and-attendance API: employees clock in and out on site (checked against a GPS geofence), managers view timesheets, and payroll exports a CSV of hours and gross pay.

**Stack:** Python 3.12 · Flask · SQLAlchemy 2 · Alembic · Postgres · Redis · Pydantic · pytest · Docker · GitHub Actions · Terraform (AWS)

## Run

```bash
docker compose up -d db redis
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
export FLASK_APP=wsgi.py
flask db upgrade        # after `flask db init` + `flask db migrate` the first time
flask run --port 8000
```

Or everything in Docker: `docker compose up --build`.

## Performance

Timesheet query for one employee and one month, on 100,000 seeded shifts
(`flask seed`), Postgres 16 in Docker on my laptop.

| Plan | Rows checked | Execution time |
| --- | --- | --- |
| Bitmap index scan on `(employee_id, clock_in)` | 39 | 0.999 ms |
| Sequential scan (index use disabled for the session) | 100,000 | 8.212 ms |

The composite index matches the query's filter (employee first, then a date range),
so Postgres reads only the 39 matching rows instead of scanning all 100,000 and
discarding 99,961. The gap grows with table size.