
"""Geographic incident clustering for ResQ AI.

Uses DBSCAN to identify geographic concentrations.
Outputs are descriptive decision support, not disaster predictions.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


SEVERITY_WEIGHTS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4,
}


def analyze_hotspots(
    incidents,
    radius_km=5.0,
    min_samples=3,
):
    """Cluster incidents geographically and summarize each cluster.

    radius_km:
        Maximum neighborhood radius used by DBSCAN.
    min_samples:
        Minimum number of nearby incidents to form a cluster.

    Returns:
        A tuple containing:
        1. Incident records with cluster labels.
        2. Summary table for detected geographic clusters.
    """

    if radius_km <= 0:
        raise ValueError("radius_km must be greater than zero.")

    if min_samples < 2:
        raise ValueError("min_samples must be at least 2.")

    required = {
        "incident_id",
        "latitude",
        "longitude",
        "severity",
        "city",
        "verification_status",
    }

    missing = required.difference(incidents.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    result = incidents.copy()
    result["hotspot_cluster"] = -1

    coordinates = result[["latitude", "longitude"]].apply(
        pd.to_numeric, errors="coerce"
    )

    valid = (
        coordinates["latitude"].between(-90, 90)
        & coordinates["longitude"].between(-180, 180)
    )

    valid_indices = result.index[valid]

    if len(valid_indices) >= min_samples:
        radians = np.radians(
            coordinates.loc[valid_indices, ["latitude", "longitude"]]
            .to_numpy()
        )

        model = DBSCAN(
            eps=radius_km / 6371.0088,
            min_samples=min_samples,
            metric="haversine",
            algorithm="ball_tree",
        )

        labels = model.fit_predict(radians)

        result.loc[valid_indices, "hotspot_cluster"] = labels

    result["hotspot_cluster"] = result[
        "hotspot_cluster"
    ].astype(int)

    result["severity_weight"] = (
        result["severity"].map(SEVERITY_WEIGHTS).fillna(0)
    )

    result["needs_verification"] = (
        result["verification_status"] != "Verified"
    )

    clustered = result[result["hotspot_cluster"] >= 0].copy()

    if clustered.empty:
        columns = [
            "hotspot_cluster",
            "incident_count",
            "high_critical_count",
            "unverified_count",
            "severity_weight_total",
            "latitude",
            "longitude",
            "cities",
        ]
        return result, pd.DataFrame(columns=columns)

    summary = (
        clustered.groupby("hotspot_cluster")
        .agg(
            incident_count=("incident_id", "count"),
            severity_weight_total=("severity_weight", "sum"),
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
            cities=(
                "city",
                lambda values: ", ".join(
                    sorted(values.dropna().astype(str).unique())
                ),
            ),
            unverified_count=("needs_verification", "sum"),
        )
        .reset_index()
    )

    high_critical = (
        clustered.assign(
            is_high_critical=clustered["severity"].isin(
                ["High", "Critical"]
            )
        )
        .groupby("hotspot_cluster")["is_high_critical"]
        .sum()
        .rename("high_critical_count")
    )

    summary = summary.merge(
        high_critical,
        on="hotspot_cluster",
        how="left",
    )

    summary["high_critical_count"] = (
        summary["high_critical_count"].astype(int)
    )

    summary["attention_note"] = summary.apply(
        lambda row: (
            "Review concentration of high/critical reports"
            if row["high_critical_count"] > 0
            else "Geographic concentration detected; review reports"
        ),
        axis=1,
    )

    summary = summary.sort_values(
        ["high_critical_count", "incident_count"],
        ascending=False,
    ).reset_index(drop=True)

    return result, summary
