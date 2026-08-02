"""
SQLite schema definitions and database operations for llmXive metadata registry.
Implements T004: Setup SQLite schema for metadata registry (tables: subjects, files).
"""

import sqlite3
import os
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any

def get_schema() -> str:
    """Return the SQL schema for the metadata registry."""
    return """
    -- Subjects table: tracks research participants
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT
    );
    
    -- Files table: indexes all artifacts in the data/ directory
    -- Does NOT store raw data, only metadata and checksums
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id TEXT,
        file_path TEXT NOT NULL,
        checksum TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'registered',
        artifact_type TEXT NOT NULL DEFAULT 'unknown',
        metadata TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        modified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
    );
    
    -- Indexes for common queries
    CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path);
    CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
    CREATE INDEX IF NOT EXISTS idx_files_subject ON files(subject_id);
    CREATE INDEX IF NOT EXISTS idx_files_type ON files(artifact_type);
    """

def init_db(db_path: Path) -> None:
    """
    Initialize the SQLite database with the required schema.
    
    Args:
        db_path: Path to the SQLite database file
    """
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute schema
    cursor.executescript(get_schema())
    
    conn.commit()
    conn.close()

def ensure_subject(db_path: Path, subject_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Ensure a subject exists in the database, creating if necessary.
    
    Args:
        db_path: Path to the SQLite database file
        subject_id: Unique subject identifier
        metadata: Optional metadata dictionary
        
    Returns:
        True if subject was created, False if already existed
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM subjects WHERE subject_id = ?", (subject_id,))
    exists = cursor.fetchone() is not None
    
    if not exists:
        metadata_json = json.dumps(metadata) if metadata else None
        cursor.execute(
            "INSERT INTO subjects (subject_id, metadata) VALUES (?, ?)",
            (subject_id, metadata_json)
        )
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def register_file(
    db_path: Path,
    file_path: str,
    checksum: str,
    status: str = 'registered',
    artifact_type: str = 'unknown',
    metadata: Optional[Dict[str, Any]] = None,
    subject_id: Optional[str] = None
) -> None:
    """
    Register a file in the metadata registry.
    
    Args:
        db_path: Path to the SQLite database file
        file_path: Relative or absolute path to the file
        checksum: SHA-256 hash of the file
        status: Current status of the file
        artifact_type: Type of artifact (code, data, test, spec, config)
        metadata: Optional metadata dictionary
        subject_id: Optional associated subject ID
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if file already exists
    cursor.execute("SELECT id FROM files WHERE file_path = ?", (file_path,))
    existing = cursor.fetchone()
    
    metadata_json = json.dumps(metadata) if metadata else None
    
    if existing:
        # Update existing record
        cursor.execute("""
            UPDATE files 
            SET checksum = ?, status = ?, artifact_type = ?, 
                metadata = ?, subject_id = ?, modified_at = CURRENT_TIMESTAMP
            WHERE file_path = ?
        """, (checksum, status, artifact_type, metadata_json, subject_id, file_path))
    else:
        # Insert new record
        cursor.execute("""
            INSERT INTO files 
            (file_path, checksum, status, artifact_type, metadata, subject_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_path, checksum, status, artifact_type, metadata_json, subject_id))
    
    conn.commit()
    conn.close()

def update_file_status(db_path: Path, file_path: str, status: str) -> None:
    """
    Update the status of a registered file.
    
    Args:
        db_path: Path to the SQLite database file
        file_path: Path to the file
        status: New status value
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE files 
        SET status = ?, modified_at = CURRENT_TIMESTAMP
        WHERE file_path = ?
    """, (status, file_path))
    
    conn.commit()
    conn.close()

def get_files_by_status(db_path: Path, status: str) -> List[Dict[str, Any]]:
    """
    Retrieve all files with a specific status.
    
    Args:
        db_path: Path to the SQLite database file
        status: Status to filter by
        
    Returns:
        List of file records as dictionaries
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM files WHERE status = ?
    """, (status,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# Import json here to avoid circular imports in module-level scope
import json