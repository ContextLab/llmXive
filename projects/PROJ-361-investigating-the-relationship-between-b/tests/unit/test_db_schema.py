import sqlite3
import os
import tempfile
from pathlib import Path
import pytest

# Mock the DB_PATH to use a temporary file for testing
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from utils.db_schema import (
    get_schema,
    init_db,
    ensure_subject,
    register_file,
    update_file_status,
    get_files_by_status,
    calculate_file_hash
)

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    # Patch the DB_PATH temporarily
    original_path = None
    # We can't easily patch the module-level constant, so we'll test the logic directly
    # by creating a connection to the temp db and running the schema manually
    conn = sqlite3.connect(db_path)
    conn.execute(get_schema())
    conn.commit()
    
    yield conn, db_path
    
    conn.close()
    os.unlink(db_path)

def test_get_schema():
    """Test that schema is returned correctly."""
    schema = get_schema()
    assert "CREATE TABLE IF NOT EXISTS subjects" in schema
    assert "CREATE TABLE IF NOT EXISTS files" in schema
    assert "subject_id TEXT PRIMARY KEY" in schema
    assert "file_path TEXT NOT NULL" in schema
    assert "checksum TEXT NOT NULL" in schema
    assert "status TEXT NOT NULL" in schema

def test_ensure_subject(temp_db):
    """Test that subjects are created correctly."""
    conn, _ = temp_db
    ensure_subject(conn, "sub-001")
    
    cursor = conn.cursor()
    cursor.execute("SELECT subject_id FROM subjects WHERE subject_id = ?", ("sub-001",))
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == "sub-001"

def test_register_file(temp_db):
    """Test file registration."""
    conn, _ = temp_db
    
    # Create a temporary file to register
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_file = f.name
    
    try:
        register_file(conn, "sub-002", temp_file)
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT subject_id, file_path, checksum, status FROM files WHERE subject_id = ?",
            ("sub-002",)
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "sub-002"
        assert result[3] == "pending"
    finally:
        os.unlink(temp_file)

def test_update_file_status(temp_db):
    """Test status updates."""
    conn, _ = temp_db
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_file = f.name
    
    try:
        register_file(conn, "sub-003", temp_file)
        update_file_status(conn, temp_file, "processed")
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status FROM files WHERE file_path = ?",
            (temp_file,)
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "processed"
    finally:
        os.unlink(temp_file)

def test_get_files_by_status(temp_db):
    """Test filtering files by status."""
    conn, _ = temp_db
    
    with tempfile.NamedTemporaryFile(delete=False) as f1:
        f1.write(b"content1")
        file1 = f1.name
    
    with tempfile.NamedTemporaryFile(delete=False) as f2:
        f2.write(b"content2")
        file2 = f2.name
    
    try:
        register_file(conn, "sub-004", file1, "pending")
        register_file(conn, "sub-005", file2, "processed")
        
        pending_files = get_files_by_status(conn, "pending")
        assert len(pending_files) == 1
        assert pending_files[0]["file_path"] == file1
        
        processed_files = get_files_by_status(conn, "processed")
        assert len(processed_files) == 1
        assert processed_files[0]["file_path"] == file2
    finally:
        os.unlink(file1)
        os.unlink(file2)

def test_calculate_file_hash():
    """Test file hash calculation."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_file = f.name
    
    try:
        hash1 = calculate_file_hash(temp_file)
        hash2 = calculate_file_hash(temp_file)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    finally:
        os.unlink(temp_file)
