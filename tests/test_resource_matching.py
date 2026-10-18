
import pandas as pd
import pytest

from src.resource_matching import recommend_resources


@pytest.fixture
def incident():
    return {
        "incident_id": "INC-001",
        "incident_type": "Flood",
        "latitude": 19.0760,
        "longitude": 72.8777,
    }


@pytest.fixture
def resources():
    return pd.DataFrame([
        {
            "resource_id": "R1",
            "type": "Rescue Team",
            "latitude": 19.0800,
            "longitude": 72.8800,
            "capabilities": "Water Rescue, Evacuation",
            "availability": "Available",
            "capacity": 10,
        },
        {
            "resource_id": "R2",
            "type": "Fire Unit",
            "latitude": 19.0770,
            "longitude": 72.8780,
            "capabilities": "Firefighting",
            "availability": "Available",
            "capacity": 5,
        },
        {
            "resource_id": "R3",
            "type": "Rescue Boat",
            "latitude": 19.0900,
            "longitude": 72.8900,
            "capabilities": "Water Rescue",
            "availability": "Unavailable",
            "capacity": 8,
        },
    ])


def test_recommends_compatible_available_resources(incident, resources):
    result = recommend_resources(incident, resources)

    assert "R1" in result["resource_id"].values
    assert "R2" not in result["resource_id"].values
    assert "R3" not in result["resource_id"].values


def test_nearest_eligible_resource_ranks_first(incident, resources):
    result = recommend_resources(incident, resources)

    assert result.iloc[0]["resource_id"] == "R1"


def test_recommendations_explain_their_reason(incident, resources):
    result = recommend_resources(incident, resources)

    assert not result.empty
    assert result["recommendation_reason"].str.contains(
        "Capability match"
    ).all()
    assert result["requires_human_review"].all()


def test_distance_limit_filters_resources(incident, resources):
    result = recommend_resources(
        incident, resources, max_distance_km=0.1
    )

    assert result.empty


def test_invalid_distance_limit_is_rejected(incident, resources):
    with pytest.raises(ValueError):
        recommend_resources(
            incident, resources, max_distance_km=0
        )
