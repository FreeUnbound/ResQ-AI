
from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

from src.database import (
    initialize_database,
    get_incidents,
    create_incident,
    update_incident,
    get_audit_log,
)

from src.priority import assess_priority

from src.hotspots import analyze_hotspots

from src.resource_matching import recommend_resources

from src.database import (
    initialize_database,
    get_incidents,
    get_resources,
    get_resource_assignments,
    create_resource_assignment,
    release_resource_assignment,
    get_audit_log,
    create_incident,
    update_incident,
)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="ResQ AI | Operations Center",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "synthetic"
INCIDENTS_FILE = DATA_DIR / "incidents.csv"
RESOURCES_FILE = DATA_DIR / "resources.csv"

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.18);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------

@st.cache_data
def load_data():
    
    incidents = pd.read_csv(INCIDENTS_FILE)
    resources = get_resources()

    incidents["timestamp"] = pd.to_datetime(
        incidents["timestamp"], errors="coerce"
    )

    for column in ["latitude", "longitude", "people_affected"]:
        incidents[column] = pd.to_numeric(
            incidents[column], errors="coerce"
        )

    for column in ["latitude", "longitude", "capacity"]:
        resources[column] = pd.to_numeric(
            resources[column], errors="coerce"
        )

    return incidents, resources


def add_priority_columns(incidents):
    """Add explainable priority results without modifying stored records."""
    incidents = incidents.copy()

    def assess_row(row):
        people = (
            int(row["people_affected"])
            if pd.notna(row["people_affected"])
            else 0
        )

        return assess_priority(
            severity=str(row["severity"]),
            people_affected=people,
            verification_status=str(row["verification_status"]),
        )

    results = incidents.apply(assess_row, axis=1)

    incidents["priority_score"] = [
        result["priority_score"] for result in results
    ]
    incidents["priority_level"] = [
        result["priority_level"] for result in results
    ]
    incidents["priority_reasons"] = [
        "; ".join(result["reasons"]) for result in results
    ]
    incidents["review_flags"] = [
        "; ".join(result["review_flags"]) or "None"
        for result in results
    ]
    incidents["requires_human_review"] = [
        result["requires_human_review"] for result in results
    ]

    return incidents

st.title("🚨 ResQ AI")
st.caption("Disaster Response Intelligence and Operations Center")

if not INCIDENTS_FILE.exists() or not RESOURCES_FILE.exists():
    st.error("Demo datasets were not found.")
    st.code("python src\\generate_data.py")
    st.stop()

try:
    initialize_database()
    incidents = get_incidents()
    resources = get_resources()

    incidents["timestamp"] = pd.to_datetime(
    incidents["timestamp"], errors="coerce"
    )
    incidents = add_priority_columns(incidents)
except Exception as exc:
    st.error(f"Could not load the datasets: {exc}")
    st.stop()

st.warning(
    "DEMO MODE: All incident and resource records are synthetic. "
    "Map locations are approximate. No live emergency feeds or "
    "real-world dispatch systems are connected."
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("🧭 Navigation")

page = st.sidebar.radio(
    "Select a section",
    [
        "Overview",
        "Incident Management",
        "Hotspot Detection",
        "Resource Allocation",
        "Data Explorer",
    ],
)

st.sidebar.divider()
st.sidebar.caption("ResQ AI | Demonstration Prototype")
st.sidebar.caption(f"Incident records: {len(incidents)}")
st.sidebar.caption(f"Resource records: {len(resources)}")

if st.sidebar.button("Refresh data", use_container_width=True):
    load_data.clear()
    st.rerun()


# --------------------------------------------------
# SHARED HELPERS
# --------------------------------------------------

def make_map(data, color_column="severity"):
    """Create an interactive map from incident coordinates."""

    valid = data.dropna(subset=["latitude", "longitude"])

    if valid.empty:
        st.info("No valid coordinates are available to map.")
        return

    center = [
        valid["latitude"].mean(),
        valid["longitude"].mean(),
    ]

    map_object = folium.Map(
        location=center,
        zoom_start=5,
        tiles="CartoDB positron",
    )

    colors = {
        "Critical": "red",
        "High": "orange",
        "Medium": "blue",
        "Low": "green",
    }

    for _, row in valid.iterrows():
        severity = str(row.get("severity", "Unknown"))
        popup_text = (
            f"ID: {row['incident_id']}<br>"
            f"Type: {row['incident_type']}<br>"
            f"Severity: {severity}<br>"
            f"City: {row['city']}<br>"
            f"Status: {row['incident_status']}<br>"
            f"Verification: {row['verification_status']}"
        )

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=7,
            color=colors.get(severity, "gray"),
            fill=True,
            fill_opacity=0.75,
            tooltip=str(row["incident_id"]),
            popup=folium.Popup(popup_text, max_width=300),
        ).add_to(map_object)

    st_folium(
        map_object,
        use_container_width=True,
        height=480,
        key=f"incident_map_{page}",
    )


# --------------------------------------------------
# OVERVIEW
# --------------------------------------------------

if page == "Overview":
    st.header("Emergency Operations Overview")

    total_incidents = len(incidents)

    high_critical = incidents["severity"].isin(
        ["High", "Critical"]
    ).sum()

    active_incidents = (
        incidents["incident_status"] != "Resolved"
    ).sum()

    available_resources = (
        resources["availability_status"] == "Available"
    ).sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Incidents", f"{total_incidents:,}")
    col2.metric("High / Critical", f"{high_critical:,}")
    col3.metric("Unresolved Incidents", f"{active_incidents:,}")
    col4.metric("Available Resources", f"{available_resources:,}")

    st.caption(
        "Metrics are calculated from the loaded demonstration datasets."
    )

    st.divider()

    left, right = st.columns([3, 2])

    with left:
        st.subheader("Incident Locations")
        make_map(incidents)

        st.caption(
            "Marker colors: red = Critical, orange = High, "
            "blue = Medium, green = Low."
        )

    with right:
        st.subheader("Incidents by Severity")

        severity_order = ["Critical", "High", "Medium", "Low"]
        severity_counts = (
            incidents["severity"]
            .value_counts()
            .reindex(severity_order, fill_value=0)
            .rename_axis("Severity")
            .reset_index(name="Incidents")
        )

        fig = px.bar(
            severity_counts,
            x="Severity",
            y="Incidents",
            color="Severity",
            category_orders={"Severity": severity_order},
            title="Severity Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Resource Availability")

        resource_counts = (
            resources["availability_status"]
            .value_counts()
            .rename_axis("Availability")
            .reset_index(name="Resources")
        )

        resource_fig = px.pie(
            resource_counts,
            names="Availability",
            values="Resources",
            hole=0.45,
            title="Resource Status",
        )
        st.plotly_chart(resource_fig, use_container_width=True)

    st.divider()
    st.subheader("Incident Trend")

    daily = (
        incidents.dropna(subset=["timestamp"])
        .assign(Date=lambda df: df["timestamp"].dt.date)
        .groupby("Date")
        .size()
        .reset_index(name="Incidents")
        .sort_values("Date")
    )

    if not daily.empty:
        trend = px.line(
            daily,
            x="Date",
            y="Incidents",
            markers=True,
            title="Reported Demo Incidents by Date",
        )
        st.plotly_chart(trend, use_container_width=True)

    st.subheader("Recent Demo Incidents")

    recent = incidents.sort_values(
        "timestamp", ascending=False
    ).head(10)

    st.dataframe(
        recent[
            [
                "incident_id",
                "timestamp",
                "city",
                "incident_type",
                "severity",
                "priority_score",
                "priority_level",
                "verification_status",
                "review_flags",
                "incident_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# INCIDENT MANAGEMENT
# --------------------------------------------------


elif page == "Incident Management":
    st.header("📋 Incident Management")

    with st.expander("➕ Register a New Incident", expanded=False):
        with st.form("new_incident_form"):
            col1, col2 = st.columns(2)

            with col1:
                city = st.selectbox(
                    "City",
                    [
                        "Mumbai", "Pune", "Delhi", "Chennai",
                        "Bengaluru", "Kolkata", "Guwahati",
                        "Ahmedabad", "Hyderabad", "Bhubaneswar",
                    ],
                )
                incident_type = st.selectbox(
                    "Incident type",
                    [
                        "Flood", "Fire", "Road Accident",
                        "Building Collapse", "Medical Emergency",
                        "Landslide", "Cyclone Damage",
                    ],
                )
                severity = st.selectbox(
                    "Reported severity",
                    ["Low", "Medium", "High", "Critical"],
                )

            with col2:
                verification = st.selectbox(
                    "Verification",
                    ["Pending", "Verified", "Unverified"],
                )
                people_affected = st.number_input(
                    "People affected",
                    min_value=0,
                    max_value=100000,
                    value=0,
                    step=1,
                )

            description = st.text_area(
                "Incident description",
                max_chars=1000,
                placeholder="Describe the reported situation...",
            )

            submitted = st.form_submit_button(
                "Register incident",
                type="primary",
            )

            if submitted:
                if not description.strip():
                    st.error("Please enter an incident description.")
                else:
                    city_coordinates = {
                        "Mumbai": (19.0760, 72.8777),
                        "Pune": (18.5204, 73.8567),
                        "Delhi": (28.6139, 77.2090),
                        "Chennai": (13.0827, 80.2707),
                        "Bengaluru": (12.9716, 77.5946),
                        "Kolkata": (22.5726, 88.3639),
                        "Guwahati": (26.1445, 91.7362),
                        "Ahmedabad": (23.0225, 72.5714),
                        "Hyderabad": (17.3850, 78.4867),
                        "Bhubaneswar": (20.2961, 85.8245),
                    }

                    latitude, longitude = city_coordinates[city]

                    record = {
                        "timestamp": pd.Timestamp.now().isoformat(
                            timespec="seconds"
                        ),
                        "city": city,
                        "latitude": latitude,
                        "longitude": longitude,
                        "incident_type": incident_type,
                        "description": description.strip(),
                        "severity": severity,
                        "verification_status": verification,
                        "incident_status": "Reported",
                        "people_affected": int(people_affected),
                    }

                    try:
                        incident_id = create_incident(record)
                        st.session_state["created_incident_id"] = (
                            incident_id
                        )
                        st.success(
                            f"Incident {incident_id} registered successfully."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not register incident: {exc}")

    incidents = get_incidents()
    incidents["timestamp"] = pd.to_datetime(
        incidents["timestamp"], errors="coerce"
    )
    incidents = add_priority_columns(incidents)

    st.subheader("Search and Filter")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_city = st.selectbox(
            "Filter city",
            ["All"] + sorted(incidents["city"].dropna().unique()),
        )

    with col2:
        selected_severity = st.selectbox(
            "Filter severity",
            ["All", "Critical", "High", "Medium", "Low"],
        )

    with col3:
        selected_status = st.selectbox(
            "Filter status",
            [
                "All", "Reported", "Under Review",
                "In Progress", "Resolved",
            ],
        )

    search_id = st.text_input("Search incident ID")

    filtered = incidents.copy()

    if selected_city != "All":
        filtered = filtered[filtered["city"] == selected_city]

    if selected_severity != "All":
        filtered = filtered[
            filtered["severity"] == selected_severity
        ]

    if selected_status != "All":
        filtered = filtered[
            filtered["incident_status"] == selected_status
        ]

    if search_id.strip():
        filtered = filtered[
            filtered["incident_id"].str.contains(
                search_id.strip(), case=False, na=False
            )
        ]

    st.write(f"**Matching incidents:** {len(filtered)}")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.subheader("Update an Incident")

    if incidents.empty:
        st.info("No incidents are available.")
    else:
        incident_ids = incidents["incident_id"].tolist()

        selected_id = st.selectbox(
            "Choose incident",
            incident_ids,
        )

        selected_record = incidents[
            incidents["incident_id"] == selected_id
        ].iloc[0]

        st.caption(
            f"Current status: {selected_record['incident_status']} | "
            f"Verification: {selected_record['verification_status']}"
        )

        with st.form("update_incident_form"):
            new_status = st.selectbox(
                "New incident status",
                [
                    "Reported", "Under Review",
                    "In Progress", "Resolved",
                ],
                index=[
                    "Reported", "Under Review",
                    "In Progress", "Resolved",
                ].index(selected_record["incident_status"]),
            )

            new_verification = st.selectbox(
                "New verification status",
                ["Pending", "Verified", "Unverified"],
                index=[
                    "Pending", "Verified", "Unverified"
                ].index(selected_record["verification_status"]),
            )

            update_submitted = st.form_submit_button(
                "Save changes",
                type="primary",
            )

            if update_submitted:
                try:
                    update_incident(
                        selected_id,
                        new_status,
                        new_verification,
                    )
                    st.success(
                        f"{selected_id} updated successfully."
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not update incident: {exc}")

    st.divider()
    st.subheader("Audit History")

    audit_id = st.selectbox(
        "Incident history",
        ["All incidents"] + incidents["incident_id"].tolist(),
    )

    if audit_id == "All incidents":
        audit = get_audit_log()
    else:
        audit = get_audit_log(audit_id)

    st.dataframe(
        audit,
        use_container_width=True,
        hide_index=True,
    )

    st.header("📋 Incident Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        city_options = ["All"] + sorted(
            incidents["city"].dropna().unique().tolist()
        )
        selected_city = st.selectbox("City", city_options)

    with col2:
        severity_options = ["All", "Critical", "High", "Medium", "Low"]
        selected_severity = st.selectbox(
            "Severity", severity_options
        )

    with col3:
        status_options = ["All"] + sorted(
            incidents["incident_status"].dropna().unique().tolist()
        )
        selected_status = st.selectbox(
            "Incident status", status_options
        )

    filtered = incidents.copy()

    if selected_city != "All":
        filtered = filtered[filtered["city"] == selected_city]

    if selected_severity != "All":
        filtered = filtered[
            filtered["severity"] == selected_severity
        ]

    if selected_status != "All":
        filtered = filtered[
            filtered["incident_status"] == selected_status
        ]

    search_id = st.text_input("Search by incident ID")

    if search_id.strip():
        filtered = filtered[
            filtered["incident_id"].str.contains(
                search_id.strip(), case=False, na=False
            )
        ]

    st.write(f"**Matching incidents:** {len(filtered)}")

    st.dataframe(
        filtered.sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download filtered incidents (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="resq_ai_filtered_incidents.csv",
        mime="text/csv",
    )

    st.info(
        "Incident creation, validation workflows and persistent status "
        "updates will be implemented in the next development milestone."
    )


# --------------------------------------------------
# HOTSPOT DETECTION
# --------------------------------------------------

elif page == "Hotspot Detection":
    st.header("📍 Geographic Hotspot Detection")
    st.caption(
        "DBSCAN identifies geographic concentrations of incident reports. "
        "This is descriptive analysis, not disaster prediction."
    )

    radius_km = st.slider(
        "Cluster radius (km)",
        min_value=1.0,
        max_value=20.0,
        value=5.0,
        step=1.0,
    )

    min_samples = st.slider(
        "Minimum reports to form a cluster",
        min_value=2,
        max_value=10,
        value=3,
        step=1,
    )

    labeled, summary = analyze_hotspots(
        incidents,
        radius_km=radius_km,
        min_samples=min_samples,
    )

    clustered = labeled[labeled["hotspot_cluster"] >= 0]
    cluster_count = summary["hotspot_cluster"].nunique()
    high_critical = (
        summary["high_critical_count"].sum()
        if not summary.empty else 0
    )
    needs_verification = (
        int(labeled["verification_status"].ne("Verified").sum())
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Reports in clusters", len(clustered))
    col2.metric("Clusters detected", cluster_count)
    col3.metric("High/Critical in clusters", int(high_critical))
    col4.metric("Reports needing verification", needs_verification)

    st.divider()

    st.subheader("Geographic Cluster Map")

    import folium
    from streamlit_folium import st_folium

    valid_map_data = labeled.dropna(
        subset=["latitude", "longitude"]
    ).copy()

    valid_map_data = valid_map_data[
        valid_map_data["latitude"].between(-90, 90)
        & valid_map_data["longitude"].between(-180, 180)
    ]

    if not valid_map_data.empty:
        center = [
            valid_map_data["latitude"].mean(),
            valid_map_data["longitude"].mean(),
        ]

        hotspot_map = folium.Map(
            location=center,
            zoom_start=5,
            tiles="OpenStreetMap",
        )

        cluster_colors = [
            "blue", "green", "purple", "orange", "darkred",
            "cadetblue", "darkgreen", "pink", "darkblue",
        ]

        for _, row in valid_map_data.iterrows():
            cluster_id = int(row["hotspot_cluster"])

            if cluster_id == -1:
                color = "gray"
                cluster_label = "Unclustered report"
            else:
                color = cluster_colors[
                    cluster_id % len(cluster_colors)
                ]
                cluster_label = f"Cluster {cluster_id}"

            popup_text = (
                f"Incident: {row['incident_id']}<br>"
                f"City: {row['city']}<br>"
                f"Severity: {row['severity']}<br>"
                f"Verification: {row['verification_status']}<br>"
                f"Group: {cluster_label}"
            )

            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=7,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.75,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{row['incident_id']} | {cluster_label}",
            ).add_to(hotspot_map)

        st_folium(
            hotspot_map,
            width=None,
            height=500,
            key="resq_hotspot_map",
        )
    else:
        st.info("No valid coordinates are available to display.")

    st.subheader("Detected Cluster Summary")

    if not summary.empty:
        chart = px.bar(
            summary,
            x="hotspot_cluster",
            y="incident_count",
            color="high_critical_count",
            hover_data=[
                "cities",
                "unverified_count",
                "severity_weight_total",
            ],
            labels={
                "hotspot_cluster": "Cluster ID",
                "incident_count": "Incident Reports",
                "high_critical_count": "High/Critical Reports",
                "cities": "Cities",
                "unverified_count": "Reports Needing Verification",
            },
            title="Reports by Geographic Cluster",
        )
        st.plotly_chart(chart, use_container_width=True)

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "No clusters were detected with the current settings. "
            "Try a larger radius or a lower minimum report count."
        )

    st.subheader("Incident-Level Cluster Assignments")

    display_columns = [
        "incident_id",
        "city",
        "severity",
        "verification_status",
        "hotspot_cluster",
    ]

    if "priority_score" in labeled.columns:
        display_columns.append("priority_score")

    st.dataframe(
        labeled[display_columns].sort_values(
            ["hotspot_cluster", "severity"],
            ascending=[True, False],
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download Cluster Analysis CSV",
        data=labeled.to_csv(index=False).encode("utf-8"),
        file_name="resq_ai_hotspot_analysis.csv",
        mime="text/csv",
    )

    st.warning(
        "Demo limitation: these clusters describe the geographic "
        "concentration of synthetic or entered reports. They are not "
        "validated disaster hotspots, forecasts, or dispatch instructions. "
        "Cluster results depend on the selected radius and minimum report "
        "count. Human review is required."
    )




# --------------------------------------------------
# RESOURCE ALLOCATION
# --------------------------------------------------

elif page == "Resource Allocation":
    st.header("🚑 Resource Allocation")
    st.caption(
        "Explainable recommendations and coordinator-controlled "
        "resource assignments."
    )

    # Always use effective database availability.
    resources = get_resources()
    incidents = get_incidents()
    incidents["timestamp"] = pd.to_datetime(
        incidents["timestamp"], errors="coerce"
    )
    incidents = add_priority_columns(incidents)

    if incidents.empty:
        st.info("No incidents are available.")
    elif resources.empty:
        st.info("No resources are available.")
    else:
        incident_ids = incidents["incident_id"].astype(str).tolist()

        selected_id = st.selectbox(
            "Select an incident",
            options=incident_ids,
            key="allocation_incident",
        )

        selected_row = incidents[
            incidents["incident_id"].astype(str) == selected_id
        ].iloc[0]

        incident_data = selected_row.to_dict()

        st.write(f"**City:** {incident_data.get('city', 'Unknown')}")
        st.write(
            f"**Incident type:** "
            f"{incident_data.get('incident_type', 'Unknown')}"
        )
        st.write(f"**Severity:** {incident_data.get('severity', 'Unknown')}")
        st.write(
            f"**Status:** {incident_data.get('incident_status', 'Unknown')}"
        )

        max_distance_km = st.slider(
            "Maximum straight-line distance (km)",
            min_value=10,
            max_value=300,
            value=100,
            step=10,
            key="allocation_max_distance",
        )

        if st.button(
            "Find Recommended Resources",
            type="primary",
            key="find_resources",
        ):
            try:
        # Refresh availability immediately before matching.
                fresh_resources = get_resources()

                recommendations = recommend_resources(
                incident_data,
                fresh_resources,
                max_distance_km=max_distance_km,
            )

                st.session_state["resource_recommendations"] = (
                    recommendations
                )
                st.session_state["resource_recommendation_incident"] = (
                    selected_id
                )
            except (ValueError, KeyError) as exc:
                st.error(f"Could not generate recommendations: {exc}")

        recommendations = st.session_state.get(
            "resource_recommendations", pd.DataFrame()
        )
        recommendation_incident = st.session_state.get(
            "resource_recommendation_incident"
        )

        if recommendation_incident == selected_id:
            if recommendations.empty:
                st.warning("No eligible resources matched this incident.")
            else:
                st.subheader("Recommended Resources")
                st.dataframe(
                    recommendations,
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "Download Recommendations CSV",
                    data=recommendations.to_csv(index=False).encode("utf-8"),
                    file_name="resq_ai_resource_recommendations.csv",
                    mime="text/csv",
                )

                st.warning(
                    "Recommendations are not dispatch instructions. "
                    "Distances are straight-line estimates, not road travel "
                    "times. A coordinator must verify each assignment."
                )

                # Refresh the resource state before presenting assignment
                # choices so a previously assigned resource isn't offered.
                current_resources = get_resources()
                current_available = set(
                    current_resources.loc[
                        current_resources["availability_status"] == "Available",
                        "resource_id",
                    ].astype(str)
                )

                eligible = recommendations[
                    recommendations["resource_id"].astype(str).isin(
                        current_available
                    )
                ].copy()

                st.divider()
                st.subheader("Assign a Resource")

                if (
                    str(incident_data.get("incident_status", "")) == "Resolved"
                ):
                    st.info(
                        "This incident is resolved. Reopen it through "
                        "Incident Management before assigning a resource."
                    )
                elif eligible.empty:
                    st.info(
                        "No currently available recommended resources can "
                        "be assigned. Refresh recommendations if needed."
                    )
                else:
                    eligible["resource_id"] = eligible[
                        "resource_id"
                    ].astype(str)

                    resource_options = eligible["resource_id"].tolist()

                    def resource_label(resource_id):
                        row = eligible[
                            eligible["resource_id"] == resource_id
                        ].iloc[0]
                        resource_type = row.get("resource_type", "Resource")
                        distance = row.get("distance_km", "N/A")
                        return (
                            f"{resource_id} | {resource_type} | "
                            f"Distance: {distance} km"
                        )

                    with st.form("assign_resource_form"):
                        resource_id = st.selectbox(
                            "Recommended resource",
                            options=resource_options,
                            format_func=resource_label,
                        )

                        confirm_assignment = st.checkbox(
                            "I have reviewed this recommendation and "
                            "confirm the assignment."
                        )

                        assign_submitted = st.form_submit_button(
                            "Confirm Assignment",
                            type="primary",
                        )

                        if assign_submitted:
                            if not confirm_assignment:
                                st.error(
                                    "Confirm the assignment checkbox first."
                                )
                            else:
                                try:
                                    assignment_id = create_resource_assignment(
                                        selected_id,
                                        resource_id,
                                        assigned_by="Coordinator",
                                    )
                                    st.success(
                                        f"Assignment #{assignment_id} created "
                                        f"for {resource_id}."
                                    )
                                    st.rerun()
                                except (ValueError, KeyError, RuntimeError) as exc:
                                    st.error(
                                        "Assignment was not created. "
                                        f"Please refresh and review availability. "
                                        f"Details: {exc}"
                                    )
                                except Exception as exc:
                                    st.error(
                                        f"Assignment failed: {exc}"
                                    )

        # Active assignments for the selected incident.
        st.divider()
        st.subheader("Active Assignments")

        active_assignments = get_resource_assignments(
            incident_id=selected_id,
            active_only=True,
        )

        if active_assignments.empty:
            st.info("This incident has no active resource assignments.")
        else:
            st.dataframe(
                active_assignments,
                use_container_width=True,
                hide_index=True,
            )

            assignment_ids = active_assignments[
                "assignment_id"
            ].tolist()

            with st.form("release_resource_form"):
                assignment_id = st.selectbox(
                    "Select assignment to release",
                    options=assignment_ids,
                    format_func=lambda value: (
                        f"Assignment #{value} | Resource "
                        f"{active_assignments.loc[
                            active_assignments['assignment_id'] == value,
                            'resource_id'
                        ].iloc[0]}"
                    ),
                )

                confirm_release = st.checkbox(
                    "I confirm this resource can be released."
                )

                release_submitted = st.form_submit_button(
                    "Release Resource",
                )

                if release_submitted:
                    if not confirm_release:
                        st.error("Confirm the release checkbox first.")
                    else:
                        try:
                            release_resource_assignment(
                                assignment_id,
                                released_by="Coordinator",
                            )
                            st.success(
                                f"Assignment #{assignment_id} released."
                            )
                            st.rerun()
                        except (ValueError, KeyError, RuntimeError) as exc:
                            st.error(f"Could not release assignment: {exc}")
                        except Exception as exc:
                            st.error(f"Release failed: {exc}")

        # Assignment audit trail.
        st.divider()
        st.subheader("Resource Assignment History")

        assignment_history = get_resource_assignments(
            incident_id=selected_id,
            active_only=False,
        )

        if assignment_history.empty:
            st.info("No assignment history is recorded for this incident.")
        else:
            st.dataframe(
                assignment_history,
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "Assignment actions are coordinator-controlled and recorded "
            "in the database audit log. This is a synthetic-data prototype, "
            "not a live dispatch system."
        )



# --------------------------------------------------
# DATA EXPLORER
# --------------------------------------------------

elif page == "Data Explorer":
    st.header("🗃️ Data Explorer")

    dataset = st.radio(
        "Choose dataset",
        ["Incidents", "Resources"],
        horizontal=True,
    )

    if dataset == "Incidents":
        st.write(f"**Rows:** {len(incidents)}")
        st.write("**Columns:**", ", ".join(incidents.columns))
        st.dataframe(
            incidents,
            use_container_width=True,
            hide_index=True,
        )
        csv_data = incidents.to_csv(index=False).encode("utf-8")
        filename = "resq_ai_incidents.csv"
    else:
        st.write(f"**Rows:** {len(resources)}")
        st.write("**Columns:**", ", ".join(resources.columns))
        st.dataframe(
            resources,
            use_container_width=True,
            hide_index=True,
        )
        csv_data = resources.to_csv(index=False).encode("utf-8")
        filename = "resq_ai_resources.csv"

    st.download_button(
        "Download selected dataset",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
    )

    st.caption(
        "All displayed records originate from the synthetic demo datasets."
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()
st.caption(
    "ResQ AI | Human-reviewed decision support | "
    "Synthetic data | No real-world dispatch"
)
