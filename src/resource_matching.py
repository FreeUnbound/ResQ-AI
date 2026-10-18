
"""Explainable resource recommendations for ResQ AI.

This module ranks candidate resources. It does not dispatch resources.
Distances are straight-line estimates, not road travel distances.
"""

import re

import numpy as np
import pandas as pd


EARTH_RADIUS_KM = 6371.0088

# Extend these mappings as your dataset's incident types require.

CAPABILITY_KEYWORDS = {
    "flood": {
        "flood rescue",
        "water rescue",
        "flood response",
        "water transport",
        "boat",
    },
    "fire": {
        "fire suppression",
        "firefighting",
        "fire fighting",
        "fire engine",
    },
    "medical": {
        "medical",
        "ambulance",
        "first aid",
        "health",
    },
    "earthquake": {
        "earthquake response",
        "structural rescue",
        "search and rescue",
        "rubble rescue",
    },
    "road accident": {
        "medical",
        "ambulance",
        "first aid",
        "road rescue",
    },
    "landslide": {
        "landslide response",
        "search and rescue",
        "slope rescue",
    },
    "cyclone": {
        "cyclone response",
        "storm response",
        "shelter",
        "evacuation",
    },
}


AVAILABLE_VALUES = {"available", "ready", "true", "yes", "1"}


def _normalize(value):
    """Normalize text for case-insensitive matching."""
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _find_column(data, candidates, required=True):
    """Find a column using common alternative names."""
    lookup = {str(column).strip().lower(): column for column in data.columns}

    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]

    if required:
        raise ValueError(
            f"Missing a required column. Expected one of: {candidates}. "
            f"Found: {list(data.columns)}"
        )

    return None


def _distance_km(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance using the Haversine formula."""
    lat1, lon1, lat2, lon2 = np.radians(
        [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )
    a = np.clip(a, 0, 1)

    return float(
        2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
    )


def _required_capabilities(incident_type):
    incident_type = _normalize(incident_type)

    for known_type, keywords in CAPABILITY_KEYWORDS.items():
        if known_type in incident_type:
            return keywords

    # Unknown incident types are not automatically rejected.
    # Their suitability must be reviewed by a coordinator.
    return set()


def recommend_resources(incident, resources, max_distance_km=100.0):
    """Return ranked, eligible resource recommendations.

    Required incident fields:
        incident_id, incident_type, latitude, longitude

    Required resource fields:
        resource_id, type, latitude, longitude,
        capabilities, availability, capacity

    Common column aliases are accepted.
    """
    if max_distance_km <= 0:
        raise ValueError("max_distance_km must be greater than zero.")

    if not isinstance(incident, dict):
        incident = incident.to_dict()

    incident_id = incident.get("incident_id", "Unknown")
    incident_type = incident.get(
        "incident_type", incident.get("type", "")
    )

    try:
        incident_lat = float(incident["latitude"])
        incident_lon = float(incident["longitude"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("Incident must have valid latitude and longitude.")

    if (
        not np.isfinite(incident_lat)
        or not np.isfinite(incident_lon)
        or not -90 <= incident_lat <= 90
        or not -180 <= incident_lon <= 180
    ):
        raise ValueError("Incident coordinates are invalid.")

    resource_id_col = _find_column(
        resources, ["resource_id", "id"]
    )
    type_col = _find_column(
        resources, ["type", "resource_type"]
    )
    lat_col = _find_column(
        resources, ["latitude", "lat"]
    )
    lon_col = _find_column(
        resources, ["longitude", "lon", "lng"]
    )
    capabilities_col = _find_column(
        resources, ["capabilities", "capability"]
    )
    availability_col = _find_column(resources,
    ["availability", "availability_status", "status"],
    )
    
    capacity_col = _find_column(
        resources, ["capacity", "available_capacity"]
    )

    results = []
    required_capabilities = _required_capabilities(incident_type)

    for _, resource in resources.iterrows():
        resource_id = resource[resource_id_col]
        reasons = []

        availability = _normalize(resource[availability_col])
        if availability not in AVAILABLE_VALUES:
            continue

        try:
            capacity = float(resource[capacity_col])
            resource_lat = float(resource[lat_col])
            resource_lon = float(resource[lon_col])
        except (TypeError, ValueError):
            continue

        if (
            not np.isfinite(capacity)
            or capacity <= 0
            or not np.isfinite(resource_lat)
            or not np.isfinite(resource_lon)
            or not -90 <= resource_lat <= 90
            or not -180 <= resource_lon <= 180
        ):
            continue

        capability_text = _normalize(resource[capabilities_col])
        resource_type = _normalize(resource[type_col])

        distance = _distance_km(
            incident_lat,
            incident_lon,
            resource_lat,
            resource_lon,
        )

        if distance > max_distance_km:
            continue

        if required_capabilities:
            matches = sorted(
                keyword
                for keyword in required_capabilities
                if keyword in capability_text or keyword in resource_type
            )
            if not matches:
                continue

            reasons.append(
                "Capability match: " + ", ".join(matches)
            )
        else:
            reasons.append(
                "Incident type has no configured capability mapping; "
                "coordinator must confirm suitability."
            )

        reasons.append("Resource marked available.")
        reasons.append(f"Reported capacity: {capacity:g}.")
        reasons.append(f"Straight-line distance: {distance:.1f} km.")

        results.append({
            "incident_id": incident_id,
            "resource_id": resource_id,
            "resource_type": resource[ type_col ],
            "capabilities": resource[capabilities_col],
            "availability": resource[availability_col],
            "capacity": capacity,
            "distance_km": round(distance, 2),
            "recommendation_reason": " ".join(reasons),
            "requires_human_review": True,
        })

    columns = [
        "incident_id",
        "resource_id",
        "resource_type",
        "capabilities",
        "availability",
        "capacity",
        "distance_km",
        "recommendation_reason",
        "requires_human_review",
    ]

    result = pd.DataFrame(results, columns=columns)

    if not result.empty:
        result = result.sort_values(
            ["distance_km", "capacity"],
            ascending=[True, False],
        ).reset_index(drop=True)

    return result
