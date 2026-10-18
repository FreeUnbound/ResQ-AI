
import pandas as pd
import pytest

from src.hotspots import analyze_hotspots


def sample_incidents():
    return pd.DataFrame({
        "incident_id": ["A", "B", "C", "D"],
        "latitude": [19.0760, 19.0770, 19.0755, 28.6139],
        "longitude": [72.8777, 72.8780, 72.8769, 77.2090],
        "severity": ["Critical", "High", "Low", "Medium"],
        "city": ["Mumbai", "Mumbai", "Mumbai", "Delhi"],
        "verification_status": [
            "Verified", "Pending", "Unverified", "Verified"
        ],
    })


def test_nearby_incidents_form_a_cluster():
    labeled, summary = analyze_hotspots(
        sample_incidents(),
        radius_km=5,
        min_samples=3,
    )

    assert (labeled["hotspot_cluster"] >= 0).sum() == 3
    assert len(summary) == 1
    assert summary.iloc[0]["incident_count"] == 3


def test_cluster_counts_high_critical_reports():
    _, summary = analyze_hotspots(sample_incidents())

    assert summary.iloc[0]["high_critical_count"] == 2
    assert summary.iloc[0]["unverified_count"] == 2


def test_distant_incident_is_not_in_the_cluster():
    labeled, _ = analyze_hotspots(sample_incidents())

    delhi = labeled[labeled["incident_id"] == "D"].iloc[0]
    assert delhi["hotspot_cluster"] == -1


def test_invalid_radius_is_rejected():
    with pytest.raises(ValueError):
        analyze_hotspots(sample_incidents(), radius_km=0)


def test_missing_columns_are_rejected():
    with pytest.raises(ValueError):
        analyze_hotspots(pd.DataFrame({"incident_id": ["A"]}))
