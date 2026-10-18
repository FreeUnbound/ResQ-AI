# ResQ AI: System Architecture

## 1. Purpose

ResQ AI is a disaster response decision-support prototype. It organizes fictional incident reports, calculates transparent rule-based priority scores, identifies geographic concentrations, and recommends potentially suitable resources for human review.

The architecture separates the dashboard, analytical modules, data generation, and persistence layer.

## 2. High-Level Architecture

```text
+--------------------------------------------------+
|                Streamlit Dashboard               |
| Overview | Incident Management | Hotspots         |
| Resource Allocation | Data Explorer              |
+-------------------------+------------------------+
                          |
             +------------+-------------+
             |                          |
             v                          v
+-------------------------+  +----------------------+
|   Analytical Modules    |  |   Database Layer     |
|                         |  |                      |
| priority.py             |  | database.py          |
| hotspots.py             |  | SQLite               |
| resource_matching.py    |  | incidents             |
|                         |  | resources             |
|                         |  | audit_log             |
|                         |  | resource_assignments  |
+-------------------------+  +----------------------+
             ^                          ^
             |                          |
             +-------------+------------+
                           |
                  +--------v---------+
                  | Synthetic CSVs   |
                  | incidents.csv    |
                  | resources.csv    |
                  +------------------+
                           ^
                           |
                  generate_data.py
```

The diagram shows logical responsibilities, not a separate deployed service for every module. The current implementation is a local Python and Streamlit application using SQLite.

## 3. Technology Responsibilities

| Component | Responsibility |
|---|---|
| Python | Application logic and deterministic calculations |
| Streamlit | Dashboard pages, controls, tables, and user workflows |
| Pandas | Loading, filtering, transforming, and summarizing tabular data |
| NumPy | Numerical operations and geographic distance calculations |
| Scikit-learn | DBSCAN clustering for geographic hotspot analysis |
| Plotly | Interactive charts |
| Folium / streamlit-folium | Interactive maps |
| SQLite | Persistent incidents, resources, audit events, and assignments |
| Pytest | Automated verification of analytical and database behavior |

## 4. Source Module Responsibilities

### `app.py`

The application entry point. It initializes the database, loads incident and resource data, calculates incident priority fields, and presents five dashboard sections:

1. Overview
2. Incident Management
3. Hotspot Detection
4. Resource Allocation
5. Data Explorer

It coordinates user actions with the database and analytical modules.

### `src/generate_data.py`

Creates reproducible fictional demonstration datasets using a fixed random seed.

- 150 synthetic incident records
- 40 synthetic resource records
- Ten demonstration cities in India
- Incident types including flood, fire, road accident, building collapse, medical emergency, landslide, and cyclone damage

Generated records are labeled `SYNTHETIC_DEMO`. The locations are approximate offsets around city coordinates.

### `src/database.py`

Manages SQLite persistence and data access.

| Table | Purpose |
|---|---|
| `incidents` | Incident attributes, status, verification, and source |
| `resources` | Resource type, capabilities, location, availability, and capacity |
| `audit_log` | Recorded incident and resource-assignment actions |
| `resource_assignments` | Assignment status, coordinator attribution, and timestamps |

The database is stored at `data\resq_ai.db`. CSV datasets are imported when the corresponding database tables are empty, rather than being re-imported on every dashboard refresh.

The assignment workflow uses database transactions and a unique partial index to prevent one resource from having multiple active assignments simultaneously.

### `src/priority.py`

Implements deterministic, explainable incident-priority assessment.

Inputs:
- Reported severity
- Reported number of people affected
- Verification status

Outputs:
- Numeric priority score
- Priority category
- Reasons contributing to the score
- Verification-related review flags
- A human-review requirement

The score uses explicit severity points and additional points for reported affected-person thresholds. Verification status does not change the score. Unverified or pending reports receive review flags.

This is a rule-based decision-support mechanism, not a validated emergency-triage model.

### `src/hotspots.py`

Uses DBSCAN with the Haversine distance metric to group geographically nearby incident coordinates.

Inputs include incident IDs, coordinates, severity, city, and verification status. The analysis returns incident-level cluster labels and a cluster summary containing incident counts, high/critical counts, unverified counts, severity-weight totals, average coordinates, and associated cities.

The radius and minimum sample count are configurable. Unclustered incidents receive the noise label `-1`.

Clusters describe concentrations in the supplied records. They do not predict future disasters.

### `src/resource_matching.py`

Produces ranked candidate resource recommendations.

The matching process checks:
1. Resource availability.
2. Positive, valid capacity.
3. Valid coordinates.
4. Distance within the configured maximum.
5. Capability compatibility for configured incident types.

Eligible candidates are ranked by straight-line distance, then capacity. Each recommendation includes an explanation and a human-review flag.

Distances use the Haversine formula. They are not road distances or travel-time estimates. The matcher does not dispatch resources.

## 5. Data Flow

### Incident data

1. The generator writes synthetic incident records to CSV.
2. The database layer imports the records when the incidents table is empty.
3. The dashboard loads persisted incident records.
4. Priority assessment adds derived scores, categories, reasons, and review flags.
5. Users can review records, update supported fields, and inspect audit history.

### Hotspot analysis

1. Incident coordinates are validated.
2. Valid coordinates are converted to radians.
3. DBSCAN groups nearby coordinates using the configured geographic radius and minimum sample count.
4. The application displays cluster summaries and incident-level results.
5. Cluster findings remain descriptive and require interpretation by a human.

### Resource recommendations and assignments

1. A coordinator selects an incident and a maximum-distance threshold.
2. The application retrieves current resource availability.
3. The matcher filters resources and ranks eligible candidates.
4. The coordinator reviews the explanations and chooses whether to assign a resource.
5. The database validates the incident and resource, checks availability, and creates an active assignment.
6. Assignment actions are recorded in the audit log.
7. A released assignment becomes historical, and the resource may become eligible again if its underlying availability and matching criteria permit it.

## 6. Database Integrity and Auditability

The database layer includes several safeguards:

- Foreign-key relationships between assignments, incidents, and resources.
- A constraint restricting assignment status to `Active` or `Released`.
- A unique partial index preventing duplicate active assignments for the same resource.
- Transactional assignment and release operations.
- Audit events for supported changes and assignment actions.

These safeguards improve consistency within the prototype. They do not replace operational authorization, security controls, or real-world resource verification.

## 7. Run and Verify

Activate the project's virtual environment and run:

```powershell
python src\generate_data.py
streamlit run app.py
```

Run automated tests with:

```powershell
python -m pytest -v
```

The documented baseline is 28 passing tests. Re-run the suite to confirm the current state after changes.

## 8. Current Architecture Boundaries

The current prototype:

- Uses synthetic CSV data and a local SQLite database.
- Does not connect to live incident feeds or official dispatch infrastructure.
- Does not calculate road travel times or live ETAs.
- Does not forecast disasters.
- Requires human review of priority assessments and resource recommendations.
- Does not claim production-scale availability, security, or deployment on IBM Z.

Any future live-data integration or operational deployment would require separate engineering, validation, authorization, and safety assessment.
