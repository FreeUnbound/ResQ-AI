# ResQ AI

**Disaster Response Intelligence and Operations Center**

ResQ AI is a disaster response decision-support prototype that helps coordinators explore incident reports, review incident priority, identify geographic concentrations, and evaluate potential resource assignments through an interactive Streamlit dashboard.

The core is designed for disaster-response use cases across different regions, with India as the initial demonstration context.

> **Important: Demonstration only.** The current application uses synthetic demo data and approximate map locations. It is not connected to live emergency feeds, official emergency-service systems, or real-world dispatch infrastructure. Priority scores and resource recommendations support human review and are not validated emergency triage decisions.

## Features

- **Emergency Operations Overview:** View incident summaries, geographic distributions, severity, resource availability, and trends.
- **Incident Management:** Review and filter incident records, create or update incidents, and inspect audit history.
- **Explainable Priority Assessment:** Calculate deterministic priority scores from reported severity and the reported number of people affected. Verification status creates review flags without changing the score.
- **Geographic Hotspot Detection:** Apply DBSCAN clustering with a Haversine distance metric to identify geographic concentrations of incident reports.
- **Resource Allocation:** Rank eligible resources using configured capability matching, availability, capacity, straight-line distance, and a maximum-distance threshold.
- **Assignment Lifecycle:** Create and release resource assignments, prevent duplicate active allocation of the same resource, and maintain assignment history.
- **Data Explorer:** Inspect the datasets available to the dashboard.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application and analytical logic |
| Pandas and NumPy | Data manipulation and numerical operations |
| Scikit-learn | DBSCAN geographic clustering |
| Streamlit | Interactive dashboard |
| Plotly | Interactive charts |
| Folium and streamlit-folium | Interactive geographic maps |
| SQLite | Persistent records, audit history, and assignments |
| Pytest | Automated tests |

## Project Structure

```text
ResQ-AI/
├── app.py
├── requirements.txt
├── src/
│   ├── database.py
│   ├── generate_data.py
│   ├── hotspots.py
│   ├── priority.py
│   └── resource_matching.py
├── data/
│   ├── synthetic/
│   │   ├── incidents.csv
│   │   └── resources.csv
│   └── resq_ai.db
├── tests/
├── docs/
└── assets/
```

The CSV files and SQLite database are generated or maintained locally. The `docs` and `assets` folders are reserved for project documentation and supporting assets.

## Run on Windows

Open PowerShell in the project directory.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, use this for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Generate synthetic demo datasets

```powershell
python src\generate_data.py
```

The generator uses a fixed random seed to make its generated scenarios reproducible. It writes 150 fictional incident records and 40 fictional resource records to `data\synthetic`.

**Existing database warning:** Generating the CSV files does not automatically replace records already stored in `data\resq_ai.db`. The database imports CSV data when the relevant database tables are empty. Preserve the database if you need to retain existing incident edits, audit history, or assignments.

### 4. Launch the dashboard

```powershell
streamlit run app.py
```

Open the local address printed by Streamlit in your browser.

## Run the Tests

From the activated virtual environment:

```powershell
python -m pytest -v
```

The current project baseline has **28 passing automated tests**. Run the command again after changes to verify the current result.

## Suggested Demonstration Flow

1. **Overview:** Introduce the incident landscape and resource availability.
2. **Incident Management:** Select a fictional incident and explain its reported severity, verification status, and audit history.
3. **Hotspot Detection:** Adjust the clustering radius and minimum sample count; explain that clusters represent geographic concentrations, not predictions.
4. **Resource Allocation:** Generate recommendations and explain the capability, availability, capacity, and distance filters.
5. **Assign a resource:** Assign an eligible resource to an incident and show the active assignment.
6. **Release and recheck:** Release the assignment, regenerate recommendations, and demonstrate that the resource can become eligible again when its stored availability and other criteria allow it.
7. **Data Explorer:** Show the synthetic records and reinforce the prototype's data boundaries.

All demonstration records should be presented as fictional scenarios, not actual emergencies.

## Architecture at a Glance

```text
Synthetic CSV datasets
          |
          v
   SQLite database
          |
          v
  Streamlit dashboard
          |
          +--> Priority assessment
          |
          +--> Geographic clustering
          |
          +--> Resource recommendations
          |
          +--> Incident and assignment workflows
          |
          v
 Audit history and persistent records
```

- `src/generate_data.py`: creates synthetic incident and resource datasets.
- `src/database.py`: initializes SQLite tables and manages incidents, resources, audit entries, and resource assignments.
- `src/priority.py`: calculates deterministic priority scores and review flags.
- `src/hotspots.py`: clusters incident coordinates using DBSCAN.
- `src/resource_matching.py`: filters and ranks candidate resources with explainable recommendation reasons.
- `app.py`: connects these capabilities to the interactive dashboard.
- `tests/`: contains automated tests for analytical logic and assignment workflows.

## Limitations and Responsible Use

- **Synthetic data:** Records are fictional and must not be interpreted as live reports.
- **Approximate coordinates:** Map markers are generated around demonstration city coordinates.
- **No live integrations:** The prototype does not ingest official emergency feeds or dispatch resources.
- **Priority scores are rule-based:** They are not a validated clinical, emergency, or disaster-triage model.
- **Hotspots are descriptive:** Clusters indicate spatial concentrations in the supplied data; they do not forecast disasters.
- **Distance is not travel time:** Resource matching uses straight-line distance, not road networks, traffic, or live ETA.
- **Recommendations require human review:** A coordinator must independently confirm suitability and operational availability.
- **Demonstration resource data is simplified:** Capabilities, capacities, and availability do not represent verified real-world operational resources.
- **Persistence matters:** The SQLite database can retain edits and assignments after the dashboard closes. Regenerating CSV files does not refresh populated database tables automatically.

## Future Development

Potential future work, subject to validation and implementation, includes authorized data integrations, improved geographic and temporal analysis, richer audit and provenance views, deployment hardening, access controls, and operational evaluation with qualified emergency-response stakeholders.

These are future possibilities, not claims about current functionality.

## Project Status

ResQ AI is an evolving demonstration prototype. Features and limitations described here should be checked against the current code and test results before each presentation or deployment.

---
