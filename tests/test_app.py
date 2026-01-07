import copy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Keep in-memory activities data isolated between tests."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


@pytest.fixture
def client():
    return TestClient(app)


def test_get_activities_returns_data(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_adds_participant(client):
    email = "newstudent@mergington.edu"
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})
    assert response.status_code == 200
    body = response.json()
    assert "Signed up" in body["message"]
    assert email in activities["Chess Club"]["participants"]


def test_signup_duplicate_rejected(client):
    email = activities["Basketball Team"]["participants"][0]
    response = client.post("/activities/Basketball%20Team/signup", params={"email": email})
    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Student already signed up for this activity"


def test_signup_unknown_activity(client):
    response = client.post("/activities/Unknown Club/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = activities["Chess Club"]["participants"][0]
    response = client.post("/activities/Chess%20Club/unregister", params={"email": email})
    assert response.status_code == 200
    body = response.json()
    assert "Unregistered" in body["message"]
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_not_registered_rejected(client):
    email = "absent@mergington.edu"
    response = client.post("/activities/Chess%20Club/unregister", params={"email": email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not registered for this activity"
