import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        app.extensions["redis"].flushdb()


@pytest.fixture
def client(app):
    return app.test_client()


# A site in central Leeds with a 150 m geofence.
SITE = {"name": "Leeds depot", "latitude": 53.7997, "longitude": -1.5492, "radius_m": 150}
ON_SITE = {"latitude": 53.7999, "longitude": -1.5490}       # ~25 m away
OFF_SITE = {"latitude": 53.8100, "longitude": -1.5492}      # ~1.1 km away


@pytest.fixture
def site(client):
    return client.post("/api/sites", json=SITE).get_json()


@pytest.fixture
def employee(client):
    body = {"name": "Ana Silva", "email": "ana@example.com", "hourly_rate": "12.50"}
    return client.post("/api/employees", json=body).get_json()
