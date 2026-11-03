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
