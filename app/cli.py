"""`flask seed` – fill the database with realistic test data for performance work."""
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import click
from sqlalchemy import insert

from .extensions import db
from .models import Employee, Site, TimeEntry


@click.command("seed")
@click.option("--employees", default=200, show_default=True)
@click.option("--shifts", default=100_000, show_default=True)
def seed(employees, shifts):
    """Insert sites, employees and completed shifts (bulk insert, in batches)."""
    rng = random.Random(42)  # seeded, so every run produces the same data

    sites = [Site(name=f"Site {i}", latitude=53.8 + i / 100, longitude=-1.55, radius_m=150)
             for i in range(10)]
    db.session.add_all(sites)
    db.session.flush()

    emps = [Employee(name=f"Employee {i}", email=f"employee{i}@example.com",
                     hourly_rate=Decimal("12.21") + Decimal(rng.randint(0, 800)) / 100)
            for i in range(employees)]
    db.session.add_all(emps)
    db.session.flush()

    start = datetime(2025, 11, 1, tzinfo=UTC)
    batch, done = [], 0
    for _ in range(shifts):
        clock_in = start + timedelta(days=rng.randint(0, 364), hours=rng.randint(5, 14))
        batch.append({
            "employee_id": rng.choice(emps).id,
            "site_id": rng.choice(sites).id,
            "clock_in": clock_in,
            "clock_out": clock_in + timedelta(minutes=rng.randint(240, 600)),
        })
        if len(batch) == 5_000:
            db.session.execute(insert(TimeEntry), batch)
            done += len(batch)
            batch = []
    if batch:
        db.session.execute(insert(TimeEntry), batch)
        done += len(batch)

    db.session.commit()
    click.echo(f"Seeded {len(sites)} sites, {employees} employees, {done} shifts.")
