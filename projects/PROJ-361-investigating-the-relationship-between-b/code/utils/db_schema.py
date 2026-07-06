"""
SQLite schema definition for the metadata registry.

This module defines the tables and helper functions to initialize the
metadata registry database. It indexes the file-based `data/` directory
without storing raw data in SQLite.

Tables:
  - subjects: Registry of participant IDs and their status.
  - files: Registry of data files, their paths, checksums, and processing status.
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional

# Default database path relative to project root
DEFAULT_DB_PATH = "data/metadata_registry.db"


def get_schema() -> str:
    """Return the SQL schema string for the metadata registry."""
    return """
    -- Subjects table: Unique identifier for each participant
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Files table: Indexes files in the data/ directory
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        checksum TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_files_subject_id ON files(subject_id);
    CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
    """


def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Initialize the SQLite database with the required schema.

    Args:
        db_path: Path to the SQLite database file. Defaults to 'data/metadata_registry.db'.

    Returns:
        A connection to the initialized database.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.executescript(get_schema())
    conn.commit()

    return conn


def ensure_subject(conn: sqlite3.Connection, subject_id: str) -> None:
    """
    Ensure a subject exists in the registry.

    Args:
        conn: Database connection.
        subject_id: The unique subject identifier.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO subjects (subject_id, status)
        VALUES (?, 'pending')
        """,
        (subject_id,)
    )
    conn.commit()


def register_file(
    conn: sqlite3.Connection,
    subject_id: str,
    file_path: str,
    checksum: Optional[str] = None,
    status: str = "pending"
) -> None:
    """
    Register a file in the metadata registry.

    Args:
        conn: Database connection.
        subject_id: The subject owning this file.
        file_path: Relative path to the file.
        checksum: Optional checksum (e.g., MD5/SHA256) of the file content.
        status: Current processing status (e.g., 'pending', 'processed', 'failed').
    """
    ensure_subject(conn, subject_id)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO files (subject_id, file_path, checksum, status)
        VALUES (?, ?, ?, ?)
        """,
        (subject_id, file_path, checksum, status)
    )
    conn.commit()


def update_file_status(
    conn: sqlite3.Connection,
    subject_id: str,
    file_path: str,
    status: str,
    checksum: Optional[str] = None
) -> None:
    """
    Update the status and optionally the checksum of a registered file.

    Args:
        conn: Database connection.
        subject_id: The subject owning the file.
        file_path: Path to the file.
        status: New status string.
        checksum: Optional new checksum.
    """
    cursor = conn.cursor()
    if checksum:
        cursor.execute(
            """
            UPDATE files
            SET status = ?, checksum = ?, updated_at = CURRENT_TIMESTAMP
            WHERE subject_id = ? AND file_path = ?
            """,
            (status, checksum, subject_id, file_path)
        )
    else:
        cursor.execute(
            """
            UPDATE files
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE subject_id = ? AND file_path = ?
            """,
            (status, subject_id, file_path)
        )
    conn.commit()


def get_files_by_status(conn: sqlite3.Connection, status: str) -> list[dict]:
    """
    Retrieve all files with a specific status.

    Args:
        conn: Database connection.
        status: The status to filter by.

    Returns:
        List of dictionaries containing file records.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT subject_id, file_path, checksum, status
        FROM files
        WHERE status = ?
        """,
        (status,)
    )
    return [dict(row) for row in cursor.fetchall()]
