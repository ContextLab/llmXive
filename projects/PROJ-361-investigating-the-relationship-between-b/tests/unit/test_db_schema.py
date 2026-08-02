import pytest
import sqlite3
import os
import tempfile
from pathlib import Path
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.db_schema import (
    get_schema, 
    _get_conn, 
    init_db, 
    ensure_subject, 
    register_file, 
    update_file_status, 
    get_files_by_status,
    calculate_file_hash,
    DB_PATH
)

@pytest.fixture
def temp_db():
    """Creates a temporary database for testing."""
    # Use a temporary directory to avoid polluting the real data directory
    with tempfile.TemporaryDirectory() as tmpdir:
        original_db_path = DB_PATH
        # Monkey patch the global path for the duration of the test
        # Note: In a real scenario, we might refactor to accept a path argument,
        # but for now we rely on the module-level constant.
        # To strictly test without side effects, we will use a context manager approach
        # or override the constant if possible. Here we assume the test runner
        # isolates or we manually manage the file.
        
        # Actually, the simplest way for this specific constraint is to use
        # the existing DB_PATH but ensure cleanup, or better, patch the function.
        # Let's patch the _get_conn to use a temp file.
        
        temp_db_path = os.path.join(tmpdir, "test_registry.db")
        
        # Save original
        original_path = None
        import utils.db_schema
        original_path = utils.db_schema.DB_PATH
        utils.db_schema.DB_PATH = temp_db_path
        
        yield temp_db_path
        
        # Restore
        utils.db_schema.DB_PATH = original_path

def test_get_schema_contains_tables(temp_db):
    schema = get_schema()
    assert "CREATE TABLE IF NOT EXISTS subjects" in schema
    assert "CREATE TABLE IF NOT EXISTS files" in schema
    assert "subject_id" in schema
    assert "file_path" in schema
    assert "checksum" in schema
    assert "status" in schema

def test_init_db_creates_tables(temp_db):
    init_db()
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Check subjects table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
    assert cursor.fetchone() is not None
    
    # Check files table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
    assert cursor.fetchone() is not None
    
    conn.close()

def test_ensure_subject_creates_new(temp_db):
    init_db()
    ensure_subject("sub-001")
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT subject_id, status FROM subjects WHERE subject_id = ?", ("sub-001",))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "sub-001"
    assert row[1] == "pending"
    conn.close()

def test_ensure_subject_updates_existing(temp_db):
    init_db()
    ensure_subject("sub-002")
    # Call again
    ensure_subject("sub-002")
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM subjects WHERE subject_id = ?", ("sub-002",))
    count = cursor.fetchone()[0]
    assert count == 1
    conn.close()

def test_register_file(temp_db, tmp_path):
    init_db()
    # Create a dummy file
    dummy_file = tmp_path / "dummy.nii.gz"
    dummy_file.write_text("dummy data")
    
    register_file("sub-003", str(dummy_file))
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, checksum, status FROM files WHERE subject_id = ?", ("sub-003",))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == str(dummy_file)
    assert row[1] != "pending_check" # Should have computed hash
    assert row[2] == "pending"
    conn.close()

def test_update_file_status(temp_db, tmp_path):
    init_db()
    dummy_file = tmp_path / "dummy2.nii.gz"
    dummy_file.write_text("dummy data")
    register_file("sub-004", str(dummy_file))
    
    update_file_status(str(dummy_file), "processed")
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM files WHERE file_path = ?", (str(dummy_file),))
    row = cursor.fetchone()
    assert row[0] == "processed"
    conn.close()

def test_get_files_by_status(temp_db, tmp_path):
    init_db()
    dummy_file = tmp_path / "dummy3.nii.gz"
    dummy_file.write_text("dummy data")
    register_file("sub-005", str(dummy_file))
    
    files = get_files_by_status("pending")
    assert len(files) == 1
    assert files[0]["file_path"] == str(dummy_file)
    assert files[0]["status"] == "pending"
    
    update_file_status(str(dummy_file), "processed")
    files = get_files_by_status("pending")
    assert len(files) == 0
    
    files = get_files_by_status("processed")
    assert len(files) == 1

def test_calculate_file_hash(tmp_path):
    test_file = tmp_path / "hash_test.txt"
    content = "test content for hashing"
    test_file.write_text(content)
    
    hash_val = calculate_file_hash(test_file)
    assert len(hash_val) == 64 # SHA256 hex length
    assert hash_val != ""
