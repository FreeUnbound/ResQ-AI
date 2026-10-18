
import sqlite3

import pandas as pd
import pytest

import src.database as db

from src.resource_matching import recommend_resources

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Use an isolated SQLite database for each test."""
    database_path = tmp_path / "test_resq_ai.db"
    data_dir = tmp_path / "synthetic"
    data_dir.mkdir()

    incidents = pd.DataFrame([
        {
            "incident_id": "INC-0001",
            "timestamp": "2026-10-18 09:00:00",
            "city": "Pune",
            "latitude": 18.52,
            "longitude": 73.85,
            "incident_type": "Flood",
            "description": "Fictional test incident",
            "severity": "High",
            "verification_status": "Verified",
            "incident_status": "Reported",
            "people_affected": 10,
            "source": "SYNTHETIC_DEMO",
        },
        {
            "incident_id": "INC-0002",
            "timestamp": "2026-10-18 09:05:00",
            "city": "Pune",
            "latitude": 18.53,
            "longitude": 73.86,
            "incident_type": "Flood",
            "description": "Another fictional test incident",
            "severity": "Medium",
            "verification_status": "Verified",
            "incident_status": "Reported",
            "people_affected": 5,
            "source": "SYNTHETIC_DEMO",
        },
    ])
    incidents.to_csv(data_dir / "incidents.csv", index=False)

    resources = pd.DataFrame([
        {
            "resource_id": "RES-001",
            "resource_type": "Boat",
            "city": "Pune",
            "latitude": 18.52,
            "longitude": 73.85,
            "capabilities": "Flood rescue; Water transport",
            "availability_status": "Available",
            "capacity": 8,
            "source": "SYNTHETIC_DEMO",
        },
        {
            "resource_id": "RES-002",
            "resource_type": "Boat",
            "city": "Pune",
            "latitude": 18.53,
            "longitude": 73.86,
            "capabilities": "Flood rescue; Water transport",
            "availability_status": "Busy",
            "capacity": 5,
            "source": "SYNTHETIC_DEMO",
        },
    ])
    resources.to_csv(data_dir / "resources.csv", index=False)

    monkeypatch.setattr(db, "DB_PATH", database_path)
    monkeypatch.setattr(db, "DATA_DIR", data_dir)

    db.initialize_database()
    return db


def test_assign_available_resource_and_audit_it(test_db):
    assignment_id = test_db.create_resource_assignment(
        "INC-0001", "RES-001"
    )

    assert assignment_id > 0

    resource = test_db.get_resources().set_index("resource_id")
    assert resource.loc["RES-001", "availability_status"] == "Busy"

    assignments = test_db.get_resource_assignments(active_only=True)
    assert len(assignments) == 1
    assert assignments.iloc[0]["resource_id"] == "RES-001"

    audit = test_db.get_audit_log("INC-0001")
    assert "RESOURCE_ASSIGNED" in audit["action"].tolist()


def test_resource_cannot_be_assigned_twice(test_db):
    test_db.create_resource_assignment("INC-0001", "RES-001")

    with pytest.raises(ValueError, match="not available|active assignment"):
        test_db.create_resource_assignment("INC-0002", "RES-001")

    assert len(test_db.get_resource_assignments(active_only=True)) == 1


def test_release_allows_reuse_of_originally_available_resource(test_db):
    assignment_id = test_db.create_resource_assignment(
        "INC-0001", "RES-001"
    )

    test_db.release_resource_assignment(assignment_id)

    resource = test_db.get_resources().set_index("resource_id")
    assert resource.loc["RES-001", "availability_status"] == "Available"

    new_assignment_id = test_db.create_resource_assignment(
        "INC-0002", "RES-001"
    )
    assert new_assignment_id > assignment_id

    audit = test_db.get_audit_log("INC-0001")
    assert "RESOURCE_RELEASED" in audit["action"].tolist()


def test_originally_busy_resource_cannot_be_assigned(test_db):
    with pytest.raises(ValueError, match="not available"):
        test_db.create_resource_assignment("INC-0001", "RES-002")


def test_resolved_incident_cannot_receive_assignment(test_db):
    with test_db.get_connection() as connection:
        connection.execute(
            "UPDATE incidents SET incident_status = 'Resolved' "
            "WHERE incident_id = ?",
            ("INC-0001",),
        )

    with pytest.raises(ValueError, match="resolved incident"):
        test_db.create_resource_assignment("INC-0001", "RES-001")


def test_missing_incident_is_rejected(test_db):
    with pytest.raises(ValueError, match="Incident not found"):
        test_db.create_resource_assignment("INC-9999", "RES-001")


def test_missing_resource_is_rejected(test_db):
    with pytest.raises(ValueError, match="Resource not found"):
        test_db.create_resource_assignment("INC-0001", "RES-999")


def test_active_assignment_excludes_resource_from_recommendations(test_db):
    incident = {
        "incident_id": "INC-0001",
        "incident_type": "Flood",
        "latitude": 18.52,
        "longitude": 73.85,
    }

    # Initially, the available boat should be recommended.
    resources = test_db.get_resources()
    initial = recommend_resources(incident, resources, max_distance_km=100)

    assert "RES-001" in initial["resource_id"].tolist()

    # Assign the boat to the first incident.
    assignment_id = test_db.create_resource_assignment(
        "INC-0001", "RES-001"
    )
    assert assignment_id > 0

    # Fetch effective availability again from SQLite.
    resources = test_db.get_resources()
    updated = recommend_resources(incident, resources, max_distance_km=100)

    assert "RES-001" not in updated["resource_id"].tolist()


def test_released_resource_returns_to_recommendations(test_db):
    incident = {
        "incident_id": "INC-0002",
        "incident_type": "Flood",
        "latitude": 18.53,
        "longitude": 73.86,
    }

    assignment_id = test_db.create_resource_assignment(
        "INC-0001", "RES-001"
    )

    # The assigned resource should be excluded.
    resources = test_db.get_resources()
    while_assigned = recommend_resources(
        incident, resources, max_distance_km=100
    )
    assert "RES-001" not in while_assigned["resource_id"].tolist()

    # Releasing it should restore eligibility.
    test_db.release_resource_assignment(assignment_id)

    resources = test_db.get_resources()
    after_release = recommend_resources(
        incident, resources, max_distance_km=100
    )

    assert "RES-001" in after_release["resource_id"].tolist()
