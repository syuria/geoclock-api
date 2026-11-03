from conftest import OFF_SITE, ON_SITE


def clock_in(client, employee, site, where=ON_SITE):
    return client.post("/api/clock-in",
                       json={"employee_id": employee["id"], "site_id": site["id"], **where})


def clock_out(client, employee, where=ON_SITE):
    return client.post("/api/clock-out", json={"employee_id": employee["id"], **where})


def test_clock_in_on_site(client, employee, site):
    r = clock_in(client, employee, site)
    assert r.status_code == 201
    assert r.get_json()["clock_out"] is None


def test_clock_in_off_site_is_rejected(client, employee, site):
    r = clock_in(client, employee, site, where=OFF_SITE)
    assert r.status_code == 422


def test_cannot_clock_in_twice(client, employee, site):
    assert clock_in(client, employee, site).status_code == 201
    assert clock_in(client, employee, site).status_code == 409


def test_clock_out_closes_shift(client, employee, site):
    clock_in(client, employee, site)
    r = clock_out(client, employee)
    assert r.status_code == 200
    assert r.get_json()["hours"] is not None


def test_clock_out_without_shift(client, employee):
    assert clock_out(client, employee).status_code == 409


def test_unknown_employee_is_404(client, site):
    r = client.post("/api/clock-in", json={"employee_id": 999, "site_id": site["id"], **ON_SITE})
    assert r.status_code == 404


def test_invalid_body_is_400(client):
    r = client.post("/api/clock-in", json={"employee_id": "abc"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "invalid request"
