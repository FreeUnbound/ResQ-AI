
import pandas as pd

from src.resource_matching import recommend_resources


def make_incident(incident_type):
    return {
        "incident_id": "TEST-001",
        "incident_type": incident_type,
        "latitude": 19.0760,
        "longitude": 72.8777,
    }


def make_resources(records):
    return pd.DataFrame(
        records,
        columns=[
            "resource_id",
            "resource_type",
            "latitude",
            "longitude",
            "capabilities",
            "availability_status",
            "capacity",
        ],
    )


def resource(resource_id, capabilities, availability="Available",
             resource_type="Response Unit"):
    return {
        "resource_id": resource_id,
        "resource_type": resource_type,
        "latitude": 19.0800,
        "longitude": 72.8800,
        "capabilities": capabilities,
        "availability_status": availability,
        "capacity": 10,
    }


def test_flood_recommends_explicit_water_rescue_capability():
    resources = make_resources([
        resource("R1", "Flood rescue; Water transport"),
    ])

    result = recommend_resources(
        make_incident("Flood"), resources, max_distance_km=100
    )

    assert result["resource_id"].tolist() == ["R1"]
    assert "flood rescue" in result.iloc[0]["recommendation_reason"]


def test_flood_does_not_accept_generic_rescue_alone():
    resources = make_resources([
        resource("R1", "Search and rescue; Evacuation"),
        resource("R2", "Fire suppression; Rescue"),
        resource("R3", "Rescue"),
    ])

    result = recommend_resources(
        make_incident("Flood"), resources, max_distance_km=100
    )

    assert result.empty


def test_fire_matches_fire_suppression_capability():
    resources = make_resources([
        resource("R1", "Fire suppression; Rescue"),
        resource("R2", "Water transport"),
    ])

    result = recommend_resources(
        make_incident("Fire"), resources, max_distance_km=100
    )

    assert result["resource_id"].tolist() == ["R1"]


def test_unavailable_flood_resource_is_excluded():
    resources = make_resources([
        resource("R1", "Flood rescue", availability="Busy"),
        resource("R2", "Water rescue", availability="Unavailable"),
        resource("R3", "Flood rescue", availability="Available"),
    ])

    result = recommend_resources(
        make_incident("Flood"), resources, max_distance_km=100
    )

    assert result["resource_id"].tolist() == ["R3"]
