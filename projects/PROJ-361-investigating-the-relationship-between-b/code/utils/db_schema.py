import sqlite3
import os
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any

# Database file path relative to project root
DB_PATH = Path("data/metadata_registry.db")

def get_schema() -> str:
    """
    Returns the SQL schema string required to initialize the database.
    Defines tables: subjects, files.
    """
    return """
    -- Table for subject metadata
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id TEXT PRIMARY KEY,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Table for file indexing (does NOT store raw data)
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        checksum TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_files_subject ON files(subject_id);
    CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
    """

def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Initializes the SQLite database and creates tables if they don't exist.
    Returns the active connection.
    """
    if db_path is None:
        db_path = str(DB_PATH)
    
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Execute schema
    cursor.executescript(get_schema())
    conn.commit()
    
    return conn

def ensure_subject(conn: sqlite3.Connection, subject_id: str, status: str = 'active') -> None:
    """
    Ensures a subject exists in the database. If not, inserts it.
    Updates the timestamp if it already exists.
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO subjects (subject_id, status)
        VALUES (?, ?)
        ON CONFLICT(subject_id) DO UPDATE SET
            status = excluded.status,
            updated_at = CURRENT_TIMESTAMP
    """, (subject_id, status))
    conn.commit()

def register_file(conn: sqlite3.Connection, subject_id: str, file_path: str, status: str = 'pending') -> None:
    """
    Registers a new file in the files table.
    Computes the SHA-256 checksum of the file content to ensure integrity.
    """
    cursor = conn.cursor()
    
    # Compute checksum
    checksum = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                checksum.update(chunk)
        file_checksum = checksum.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Cannot compute checksum: file not found at {file_path}")
    
    # Ensure subject exists first
    ensure_subject(conn, subject_id)
    
    # Insert file record
    cursor.execute("""
        INSERT INTO files (subject_id, file_path, checksum, status)
        VALUES (?, ?, ?, ?)
    """, (subject_id, file_path, file_checksum, status))
    conn.commit()

def update_file_status(conn: sqlite3.Connection, file_path: str, status: str) -> None:
    """
    Updates the status of a specific file record.
    """
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE files
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE file_path = ?
    """, (status, file_path))
    conn.commit()

def get_files_by_status(conn: sqlite3.Connection, status: str) -> List[Dict[str, Any]]:
    """
    Retrieves all file records matching a specific status.
    Returns a list of dictionaries.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, subject_id, file_path, checksum, status, created_at
        FROM files
        WHERE status = ?
    """, (status,))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
