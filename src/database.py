
from pathlib import Path
import sqlite3

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "synthetic"
DB_PATH = ROOT / "data" / "resq_ai.db"

INCIDENT_COLUMNS = [
    "incident_id",
    "timestamp",
    "city",
    "latitude",
    "longitude",
    "incident_type",
    "description",
    "severity",
    "verification_status",
    "incident_status",
    "people_affected",
    "source",
]

RESOURCE_COLUMNS = [
    "resource_id",
    "resource_type",
    "city",
    "latitude",
    "longitude",
    "capabilities",
    "availability_status",
    "capacity",
    "source",
]

def get_connection():
    """Open a connection to the ResQ AI database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)

    connection.execute("PRAGMA foreign_keys = ON")  # Add this
    connection.execute("PRAGMA busy_timeout = 10000")

    return connection


def initialize_database():
    """Create the database and import demo data on first run."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                city TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                incident_type TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                incident_status TEXT NOT NULL,
                people_affected INTEGER DEFAULT 0,
                source TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL,
                changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS resources (
                resource_id TEXT PRIMARY KEY,
                resource_type TEXT NOT NULL,
                city TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                capabilities TEXT NOT NULL,
                availability_status TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                source TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS resource_assignments (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active'
                    CHECK (status IN ('Active', 'Released')),
                assigned_by TEXT NOT NULL DEFAULT 'Coordinator',
                assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                released_at TEXT,
                FOREIGN KEY (incident_id)
                    REFERENCES incidents(incident_id),
                FOREIGN KEY (resource_id)
                    REFERENCES resources(resource_id)
            )
            """
        )

        # Database-level protection against double allocation.
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            one_active_assignment_per_resource
            ON resource_assignments(resource_id)
            WHERE status = 'Active'
            """
        )

        # Import resources independently of the incident import.
        resource_count = connection.execute(
            "SELECT COUNT(*) FROM resources"
        ).fetchone()[0]

        if resource_count == 0:
            csv_path = DATA_DIR / "resources.csv"

            if csv_path.exists():
                resource_data = pd.read_csv(csv_path)
                resource_data = resource_data[RESOURCE_COLUMNS]

                resource_data.to_sql(
                    "resources",
                    connection,
                    if_exists="append",
                    index=False,
                )

        count = connection.execute(
            "SELECT COUNT(*) FROM incidents"
        ).fetchone()[0]

        # Import the CSV only when the database has no incidents.
        if count == 0:
            csv_path = DATA_DIR / "incidents.csv"

            if csv_path.exists():
                demo_data = pd.read_csv(csv_path)

                demo_data = demo_data[INCIDENT_COLUMNS]

                demo_data.to_sql(
                    "incidents",
                    connection,
                    if_exists="append",
                    index=False,
                )

                connection.execute(
                    """
                    INSERT INTO audit_log
                    (incident_id, action, details)
                    VALUES (?, ?, ?)
                    """,
                    (
                        "SYSTEM",
                        "INITIAL_IMPORT",
                        f"Imported {len(demo_data)} synthetic demo incidents",
                    ),
                )


def get_incidents():
    """Return all incidents from persistent storage."""
    initialize_database()

    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT * FROM incidents
            ORDER BY timestamp DESC
            """,
            connection,
        )


def create_incident(record):
    """Save a new incident and record its creation in the audit log."""
    initialize_database()

    with get_connection() as connection:
        next_number = connection.execute(
            """
            SELECT COALESCE(
                MAX(CAST(SUBSTR(incident_id, 5) AS INTEGER)), 0
            ) + 1
            FROM incidents
            WHERE incident_id GLOB 'INC-[0-9]*'
            """
        ).fetchone()[0]

        incident_id = f"INC-{next_number:04d}"

        connection.execute(
            """
            INSERT INTO incidents (
                incident_id, timestamp, city, latitude, longitude,
                incident_type, description, severity,
                verification_status, incident_status,
                people_affected, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                record["timestamp"],
                record["city"],
                record["latitude"],
                record["longitude"],
                record["incident_type"],
                record["description"],
                record["severity"],
                record["verification_status"],
                record["incident_status"],
                record["people_affected"],
                "COORDINATOR_ENTERED_DEMO",
            ),
        )

        connection.execute(
            """
            INSERT INTO audit_log (incident_id, action, details)
            VALUES (?, ?, ?)
            """,
            (
                incident_id,
                "INCIDENT_CREATED",
                "Incident entered through the ResQ AI interface",
            ),
        )

    return incident_id


def update_incident(incident_id, new_status, new_verification):
    """Update incident status and verification with an audit trail."""
    allowed_statuses = {
        "Reported",
        "Under Review",
        "In Progress",
        "Resolved",
    }

    allowed_verification = {
        "Pending",
        "Verified",
        "Unverified",
    }

    if new_status not in allowed_statuses:
        raise ValueError("Invalid incident status.")

    if new_verification not in allowed_verification:
        raise ValueError("Invalid verification status.")

    initialize_database()

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT incident_status, verification_status
            FROM incidents
            WHERE incident_id = ?
            """,
            (incident_id,),
        ).fetchone()

        if existing is None:
            raise ValueError("Incident not found.")

        old_status, old_verification = existing

        connection.execute(
            """
            UPDATE incidents
            SET incident_status = ?,
                verification_status = ?
            WHERE incident_id = ?
            """,
            (new_status, new_verification, incident_id),
        )

        connection.execute(
            """
            INSERT INTO audit_log (incident_id, action, details)
            VALUES (?, ?, ?)
            """,
            (
                incident_id,
                "INCIDENT_UPDATED",
                (
                    f"Status: {old_status} -> {new_status}; "
                    f"Verification: {old_verification} -> "
                    f"{new_verification}"
                ),
            ),
        )


def get_audit_log(incident_id=None):
    """Retrieve audit history, optionally for one incident."""
    initialize_database()

    with get_connection() as connection:
        if incident_id:
            return pd.read_sql_query(
                """
                SELECT * FROM audit_log
                WHERE incident_id = ?
                ORDER BY log_id DESC
                """,
                connection,
                params=(incident_id,),
            )

        return pd.read_sql_query(
            "SELECT * FROM audit_log ORDER BY log_id DESC",
            connection,
        )


def get_resources():
    """Return resources, marking actively assigned resources as Busy."""
    initialize_database()

    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT
                r.resource_id,
                r.resource_type,
                r.city,
                r.latitude,
                r.longitude,
                r.capabilities,
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM resource_assignments a
                        WHERE a.resource_id = r.resource_id
                          AND a.status = 'Active'
                    )
                    THEN 'Busy'
                    ELSE r.availability_status
                END AS availability_status,
                r.capacity,
                r.source
            FROM resources r
            ORDER BY r.resource_id
            """,
            connection,
        )


def get_resource_assignments(incident_id=None, active_only=False):
    """Retrieve assignment history, optionally filtered by incident/status."""
    initialize_database()

    query = """
        SELECT
            a.assignment_id,
            a.incident_id,
            i.city AS incident_city,
            i.incident_type,
            a.resource_id,
            r.resource_type,
            r.city AS resource_city,
            a.status,
            a.assigned_by,
            a.assigned_at,
            a.released_at
        FROM resource_assignments a
        JOIN incidents i ON i.incident_id = a.incident_id
        JOIN resources r ON r.resource_id = a.resource_id
    """

    conditions = []
    params = []

    if incident_id is not None:
        conditions.append("a.incident_id = ?")
        params.append(incident_id)

    if active_only:
        conditions.append("a.status = 'Active'")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY a.assignment_id DESC"

    with get_connection() as connection:
        return pd.read_sql_query(query, connection, params=params)


def create_resource_assignment(
    incident_id,
    resource_id,
    assigned_by="Coordinator",
):
    """Assign an available resource to an incident and log the action."""
    initialize_database()

    with get_connection() as connection:
        # Serialize competing assignment attempts.
        connection.execute("BEGIN IMMEDIATE")

        incident = connection.execute(
            """
            SELECT incident_status
            FROM incidents
            WHERE incident_id = ?
            """,
            (incident_id,),
        ).fetchone()

        if incident is None:
            raise ValueError("Incident not found.")

        if incident[0] == "Resolved":
            raise ValueError(
                "Cannot assign a resource to a resolved incident."
            )

        resource = connection.execute(
            """
            SELECT availability_status
            FROM resources
            WHERE resource_id = ?
            """,
            (resource_id,),
        ).fetchone()

        if resource is None:
            raise ValueError("Resource not found.")

        if resource[0].strip().lower() != "available":
            raise ValueError("Resource is not available.")

        active_assignment = connection.execute(
            """
            SELECT assignment_id
            FROM resource_assignments
            WHERE resource_id = ?
              AND status = 'Active'
            """,
            (resource_id,),
        ).fetchone()

        if active_assignment is not None:
            raise ValueError(
                "Resource already has an active assignment."
            )

        cursor = connection.execute(
            """
            INSERT INTO resource_assignments (
                incident_id,
                resource_id,
                assigned_by
            )
            VALUES (?, ?, ?)
            """,
            (incident_id, resource_id, assigned_by),
        )

        assignment_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO audit_log (incident_id, action, details)
            VALUES (?, ?, ?)
            """,
            (
                incident_id,
                "RESOURCE_ASSIGNED",
                (
                    f"Assignment {assignment_id}: resource "
                    f"{resource_id} assigned by {assigned_by}"
                ),
            ),
        )

    return assignment_id


def release_resource_assignment(
    assignment_id,
    released_by="Coordinator",
):
    """Release an active assignment and record the action."""
    initialize_database()

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        assignment = connection.execute(
            """
            SELECT incident_id, resource_id, status
            FROM resource_assignments
            WHERE assignment_id = ?
            """,
            (assignment_id,),
        ).fetchone()

        if assignment is None:
            raise ValueError("Assignment not found.")

        incident_id, resource_id, status = assignment

        if status != "Active":
            raise ValueError("Assignment is not active.")

        connection.execute(
            """
            UPDATE resource_assignments
            SET status = 'Released',
                released_at = CURRENT_TIMESTAMP
            WHERE assignment_id = ?
            """,
            (assignment_id,),
        )

        connection.execute(
            """
            INSERT INTO audit_log (incident_id, action, details)
            VALUES (?, ?, ?)
            """,
            (
                incident_id,
                "RESOURCE_RELEASED",
                (
                    f"Assignment {assignment_id}: resource "
                    f"{resource_id} released by {released_by}"
                ),
            ),
        )
