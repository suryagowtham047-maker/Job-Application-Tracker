import sqlite3
from datetime import date

DATABASE_NAME = "applications.db"

APPLICATION_STATUSES = (
    "Applied",
    "Online Assessment",
    "Interview",
    "Offered",
    "Rejected",
)

TRASH_RETENTION_DAYS = 15


def get_connection():
    """Create a SQLite connection with named-column access."""
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create the database and migrate existing databases safely."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                job_type TEXT NOT NULL DEFAULT 'Full-time',
                application_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Applied'
                    CHECK(status IN (
                        'Applied',
                        'Online Assessment',
                        'Interview',
                        'Offered',
                        'Rejected'
                    )),
                interview_date TEXT NOT NULL DEFAULT '',
                job_url TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT NOT NULL DEFAULT ''
            )
        """)

        # Add the column to an existing database created by the older version.
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(applications)"
            ).fetchall()
        }

        if "deleted_at" not in columns:
            connection.execute("""
                ALTER TABLE applications
                ADD COLUMN deleted_at TEXT NOT NULL DEFAULT ''
            """)

        # Remove records that have spent 15 days or longer in the bin.
        connection.execute("""
            DELETE FROM applications
            WHERE deleted_at != ''
              AND strftime('%s', 'now') - strftime('%s', deleted_at)
                  >= ?
        """, (TRASH_RETENTION_DAYS * 24 * 60 * 60,))


def cleanup_expired_trash():
    """Permanently delete applications that have expired in the bin."""
    with get_connection() as connection:
        cursor = connection.execute("""
            DELETE FROM applications
            WHERE deleted_at != ''
              AND strftime('%s', 'now') - strftime('%s', deleted_at)
                  >= ?
        """, (TRASH_RETENTION_DAYS * 24 * 60 * 60,))
        return cursor.rowcount


def add_application(
    company,
    role,
    location,
    job_type,
    application_date,
    status,
    interview_date="",
    job_url="",
    notes="",
):
    """Add a new active application."""
    if status not in APPLICATION_STATUSES:
        raise ValueError("Invalid application status.")

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO applications (
                company,
                role,
                location,
                job_type,
                application_date,
                status,
                interview_date,
                job_url,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company.strip(),
            role.strip(),
            location.strip(),
            job_type,
            application_date,
            status,
            interview_date,
            job_url.strip(),
            notes.strip(),
        ))
        return cursor.lastrowid


def get_all_applications(search="", status="", job_type=""):
    """Return active applications matching the supplied filters."""
    query = """
        SELECT *
        FROM applications
        WHERE deleted_at = ''
    """
    parameters = []

    if search:
        pattern = f"%{search.strip()}%"
        query += """
            AND (
                company LIKE ?
                OR role LIKE ?
                OR location LIKE ?
                OR notes LIKE ?
            )
        """
        parameters.extend([pattern, pattern, pattern, pattern])

    if status and status in APPLICATION_STATUSES:
        query += " AND status = ?"
        parameters.append(status)

    if job_type:
        query += " AND job_type = ?"
        parameters.append(job_type)

    query += """
        ORDER BY
            CASE WHEN interview_date = '' THEN 1 ELSE 0 END,
            interview_date ASC,
            application_date DESC,
            id DESC
    """

    with get_connection() as connection:
        return connection.execute(query, parameters).fetchall()


def get_application_by_id(application_id):
    """Find an active application by its ID."""
    with get_connection() as connection:
        return connection.execute("""
            SELECT *
            FROM applications
            WHERE id = ? AND deleted_at = ''
        """, (application_id,)).fetchone()


def update_application(
    application_id,
    company,
    role,
    location,
    job_type,
    application_date,
    status,
    interview_date="",
    job_url="",
    notes="",
):
    """Update an active application."""
    if status not in APPLICATION_STATUSES:
        raise ValueError("Invalid application status.")

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE applications
            SET company = ?,
                role = ?,
                location = ?,
                job_type = ?,
                application_date = ?,
                status = ?,
                interview_date = ?,
                job_url = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND deleted_at = ''
        """, (
            company.strip(),
            role.strip(),
            location.strip(),
            job_type,
            application_date,
            status,
            interview_date,
            job_url.strip(),
            notes.strip(),
            application_id,
        ))
        return cursor.rowcount


def delete_application(application_id):
    """Move an active application to the Recycle Bin."""
    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE applications
            SET deleted_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND deleted_at = ''
        """, (application_id,))
        return cursor.rowcount > 0


def get_trashed_applications():
    """Return deleted applications that have not yet expired."""
    cleanup_expired_trash()

    with get_connection() as connection:
        return connection.execute("""
            SELECT *,
                   CAST(
                       (
                           strftime('%s', deleted_at)
                           + ?
                           - strftime('%s', 'now')
                           + 86399
                       ) / 86400 AS INTEGER
                   ) AS days_remaining
            FROM applications
            WHERE deleted_at != ''
            ORDER BY deleted_at DESC, id DESC
        """, (
            TRASH_RETENTION_DAYS * 24 * 60 * 60,
        )).fetchall()


def restore_application(application_id):
    """Restore an application from the Recycle Bin."""
    cleanup_expired_trash()

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE applications
            SET deleted_at = '',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND deleted_at != ''
        """, (application_id,))
        return cursor.rowcount > 0


def permanently_delete_application(application_id):
    """Permanently delete one application from the Recycle Bin."""
    with get_connection() as connection:
        cursor = connection.execute("""
            DELETE FROM applications
            WHERE id = ? AND deleted_at != ''
        """, (application_id,))
        return cursor.rowcount > 0


def get_dashboard_stats():
    """Calculate dashboard statistics using active applications only."""
    with get_connection() as connection:
        total = connection.execute("""
            SELECT COUNT(*)
            FROM applications
            WHERE deleted_at = ''
        """).fetchone()[0]

        status_rows = connection.execute("""
            SELECT status, COUNT(*) AS count
            FROM applications
            WHERE deleted_at = ''
            GROUP BY status
        """).fetchall()

        status_counts = {
            status: 0 for status in APPLICATION_STATUSES
        }

        for row in status_rows:
            status_counts[row["status"]] = row["count"]

        upcoming_interviews = connection.execute("""
            SELECT COUNT(*)
            FROM applications
            WHERE deleted_at = ''
              AND status = 'Interview'
              AND interview_date >= ?
        """, (date.today().isoformat(),)).fetchone()[0]

        trashed_count = connection.execute("""
            SELECT COUNT(*)
            FROM applications
            WHERE deleted_at != ''
        """).fetchone()[0]

        return {
            "total": total,
            "status_counts": status_counts,
            "upcoming_interviews": upcoming_interviews,
            "trashed_count": trashed_count,
        }
