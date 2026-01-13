import json
import pytest

from app import app


@pytest.fixture()
def client():
    app.config.update({"TESTING": True})
    with app.test_client() as c:
        yield c


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert "time_utc" in body


def test_create_and_get_user(client):
    payload = {"name": "Santosh", "email": "santosh@example.com"}
    resp = client.post("/users", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 201
    created = resp.get_json()
    assert created["id"] >= 1

    resp2 = client.get(f"/users/{created['id']}")
    assert resp2.status_code == 200
    got = resp2.get_json()
    assert got["name"] == "Santosh"


def test_validation_error(client):
    resp = client.post("/users", json={"name": "", "email": "bad"})
    assert resp.status_code == 400
