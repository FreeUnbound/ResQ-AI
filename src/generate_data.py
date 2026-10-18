
from pathlib import Path
import random
import pandas as pd

# ResQ AI: Synthetic demo data generator
# All records are fictional, NOT live emergency reports.

SEED = 42
random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CITIES = {
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

INCIDENT_TYPES = [
    "Flood", "Fire", "Road Accident", "Building Collapse",
    "Medical Emergency", "Landslide", "Cyclone Damage"
]

SEVERITIES = ["Low", "Medium", "High", "Critical"]
VERIFICATION = ["Verified", "Pending", "Unverified"]
STATUSES = ["Reported", "Under Review", "In Progress", "Resolved"]

DESCRIPTIONS = {
    "Flood": "Fictional report of waterlogging affecting a local area.",
    "Fire": "Fictional report of a fire requiring assessment.",
    "Road Accident": "Fictional report of a road incident.",
    "Building Collapse": "Fictional report of structural damage.",
    "Medical Emergency": "Fictional request for medical assistance.",
    "Landslide": "Fictional report of a possible landslide.",
    "Cyclone Damage": "Fictional report of weather-related damage.",
}

# Capabilities are explicit so resource matching remains strict.
RESOURCE_TYPES = {
    "Ambulance": ["Medical aid", "Patient transport", "First aid"],
    "Fire Engine": ["Fire suppression", "Rescue"],
    "Rescue Team": ["Search and rescue", "Evacuation"],
    "Relief Truck": ["Food distribution", "Water distribution"],
    "Boat": ["Flood rescue", "Water transport"],
}

# A city-level resource pool. These are demo scenarios, not operational claims.
resources_by_incident = {
    "Flood": ["Boat"],
    "Fire": ["Fire Engine"],
    "Road Accident": ["Ambulance"],
    "Building Collapse": ["Rescue Team"],
    "Medical Emergency": ["Ambulance"],
    "Landslide": ["Rescue Team"],
    "Cyclone Damage": ["Relief Truck", "Boat"],
}

# Generate reproducible fictional incident records.
incidents = []

for i in range(1, 151):
    city = random.choice(list(CITIES.keys()))
    base_lat, base_lon = CITIES[city]
    incident_type = random.choice(INCIDENT_TYPES)
    severity = random.choices(
        SEVERITIES, weights=[25, 35, 27, 13]
    )[0]

    incidents.append({
        "incident_id": f"INC-{i:04d}",
        "timestamp": (
            f"2026-10-{random.randint(1, 18):02d} "
            f"{random.randint(0, 23):02d}:"
            f"{random.choice([0, 15, 30, 45]):02d}:00"
        ),
        "city": city,
        "latitude": round(base_lat + random.uniform(-0.08, 0.08), 6),
        "longitude": round(base_lon + random.uniform(-0.08, 0.08), 6),
        "incident_type": incident_type,
        "description": DESCRIPTIONS[incident_type],
        "severity": severity,
        "verification_status": random.choice(VERIFICATION),
        "incident_status": random.choice(STATUSES),
        "people_affected": random.randint(0, 80),
        "source": "SYNTHETIC_DEMO",
    })

incidents_df = pd.DataFrame(incidents)

# Generate a balanced set of resource types.
resource_type_names = list(RESOURCE_TYPES.keys())
resource_types = [
    resource_type_names[i % len(resource_type_names)]
    for i in range(40)
]
random.shuffle(resource_types)

# Ensure at least one available resource of each type.
availability = ["Available"] * len(resource_type_names)
availability += [
    random.choice(["Available", "Busy", "Unavailable"])
    for _ in range(40 - len(resource_type_names))
]
random.shuffle(availability)

resources = []

for i, resource_type in enumerate(resource_types, start=1):
    # Spread resources across the same city set as incidents.
    city = list(CITIES.keys())[(i - 1) % len(CITIES)]
    base_lat, base_lon = CITIES[city]

    resources.append({
        "resource_id": f"RES-{i:03d}",
        "resource_type": resource_type,
        "city": city,
        "latitude": round(base_lat + random.uniform(-0.06, 0.06), 6),
        "longitude": round(base_lon + random.uniform(-0.06, 0.06), 6),
        "capabilities": "; ".join(RESOURCE_TYPES[resource_type]),
        "availability_status": availability[i - 1],
        "capacity": random.randint(2, 20),
        "source": "SYNTHETIC_DEMO",
    })

resources_df = pd.DataFrame(resources)

incidents_path = OUTPUT_DIR / "incidents.csv"
resources_path = OUTPUT_DIR / "resources.csv"

incidents_df.to_csv(incidents_path, index=False)
resources_df.to_csv(resources_path, index=False)

print("ResQ AI synthetic datasets created successfully.")
print(f"Incidents: {len(incidents_df)} records")
print(f"Resources: {len(resources_df)} records")
print(f"Available resources: {(resources_df['availability_status'] == 'Available').sum()}")
print(f"\nSaved to: {OUTPUT_DIR}")
print("\nIncident sample:")
print(incidents_df.head(5).to_string(index=False))
print("\nResource sample:")
print(resources_df.head(5).to_string(index=False))
