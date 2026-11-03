"""Cache-aside for timesheets.

Read:  look in Redis first; on a miss, query Postgres and store the result
       with a time-to-live (TTL).
Write: when a shift changes, delete that employee's cached timesheets so
       nobody sees stale hours.
"""
import json

from flask import current_app


def _redis():
    return current_app.extensions["redis"]


def timesheet_key(employee_id, start, end):
    return f"timesheet:{employee_id}:{start}:{end}"


def get_cached(key):
    raw = _redis().get(key)
    return json.loads(raw) if raw else None


def set_cached(key, value):
    ttl = current_app.config["TIMESHEET_CACHE_SECONDS"]
    _redis().set(key, json.dumps(value), ex=ttl)


def invalidate_employee(employee_id):
    r = _redis()
    # SCAN, not KEYS: KEYS blocks Redis while it walks every key.
    for key in r.scan_iter(match=f"timesheet:{employee_id}:*"):
        r.delete(key)
