import sqlite3
import os
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "registry.db"

def get_schema() -> str:
    """Return the SQL schema definition for the metadata registry."""
    return """
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        checksum TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
    );

    CREATE INDEX IF NOT EXISTS idx_files_subject ON files(subject_id);
    CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
    """

def init_db() -> sqlite3.Connection:
    """Initialize the SQLite database and create tables if they don't exist."""
    db_path = DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.executescript(get_schema())
    conn.commit()
    
    return conn

def ensure_subject(conn: sqlite3.Connection, subject_id: str) -> None:
    """Ensure a subject exists in the registry."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO subjects (subject_id, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))",
        (subject_id,)
    )
    conn.commit()

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def register_file(
    conn: sqlite3.Connection,
    subject_id: str,
    file_path: str,
    status: str = "pending"
) -> None:
    """Register a file in the registry."""
    ensure_subject(conn, subject_id)
    
    checksum = calculate_file_hash(file_path)
    abs_path = str(Path(file_path).resolve())
    
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO files (subject_id, file_path, checksum, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (subject_id, abs_path, checksum, status)
    )
    conn.commit()

def update_file_status(
    conn: sqlite3.Connection,
    file_path: str,
    status: str
) -> None:
    """Update the status of a file in the registry."""
    abs_path = str(Path(file_path).resolve())
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE files 
        SET status = ?, updated_at = datetime('now')
        WHERE file_path = ?
        """,
        (status, abs_path)
    )
    conn.commit()

def get_files_by_status(
    conn: sqlite3.Connection,
    status: str
) -> List[Dict[str, Any]]:
    """Get all files with a specific status."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT subject_id, file_path, checksum, status FROM files WHERE status = ?",
        (status,)
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_subject_files(
    conn: sqlite3.Connection,
    subject_id: str
) -> List[Dict[str, Any]]:
    """Get all files for a specific subject."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT file_path, checksum, status FROM files WHERE subject_id = ?",
        (subject_id,)
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
