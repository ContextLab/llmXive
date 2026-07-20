import pytest
import sqlite3
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.db_schema import init_db, ensure_subject, register_file, update_file_status, get_files_by_status

@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def db_conn(temp_db):
    """Provide a connection to the temp database."""
    return init_db(temp_db)

@pytest.fixture
def sample_file(temp_db):
    """Create a temporary file to register."""
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write("test content for checksum")
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_init_db_creates_tables(db_conn):
    """Test that init_db creates the required tables."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects';")
    assert cursor.fetchone() is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files';")
    assert cursor.fetchone() is not None

def test_ensure_subject_inserts_new(db_conn):
    """Test that ensure_subject inserts a new subject if not present."""
    ensure_subject(db_conn, "sub-001")
    cursor = db_conn.cursor()
    cursor.execute("SELECT subject_id, status FROM subjects WHERE subject_id = 'sub-001';")
    row = cursor.fetchone()
    assert row is not None
    assert row['subject_id'] == 'sub-001'
    assert row['status'] == 'active'

def test_ensure_subject_updates_existing(db_conn):
    """Test that ensure_subject updates status if subject exists."""
    ensure_subject(db_conn, "sub-001", status='active')
    ensure_subject(db_conn, "sub-001", status='archived')
    
    cursor = db_conn.cursor()
    cursor.execute("SELECT status FROM subjects WHERE subject_id = 'sub-001';")
    row = cursor.fetchone()
    assert row['status'] == 'archived'

def test_register_file_creates_record(db_conn, sample_file):
    """Test that register_file creates a file record with correct checksum."""
    ensure_subject(db_conn, "sub-001")
    register_file(db_conn, "sub-001", sample_file, status='pending')
    
    cursor = db_conn.cursor()
    cursor.execute("SELECT file_path, checksum, status FROM files WHERE subject_id = 'sub-001';")
    row = cursor.fetchone()
    assert row is not None
    assert row['file_path'] == sample_file
    assert row['status'] == 'pending'
    assert len(row['checksum']) == 64  # SHA-256 hex length

def test_register_file_fails_on_missing_file(db_conn):
    """Test that register_file raises FileNotFoundError for missing files."""
    ensure_subject(db_conn, "sub-001")
    with pytest.raises(FileNotFoundError):
        register_file(db_conn, "sub-001", "/nonexistent/path/file.txt")

def test_update_file_status(db_conn, sample_file):
    """Test updating file status."""
    ensure_subject(db_conn, "sub-001")
    register_file(db_conn, "sub-001", sample_file, status='pending')
    
    update_file_status(db_conn, sample_file, 'processed')
    
    cursor = db_conn.cursor()
    cursor.execute("SELECT status FROM files WHERE file_path = ?", (sample_file,))
    row = cursor.fetchone()
    assert row['status'] == 'processed'

def test_get_files_by_status(db_conn, sample_file):
    """Test retrieving files by status."""
    ensure_subject(db_conn, "sub-001")
    register_file(db_conn, "sub-001", sample_file, status='pending')
    
    # Create another file with different status
    fd, path2 = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write("other content")
    os.close(fd)
    try:
        register_file(db_conn, "sub-001", path2, status='processed')
        
        pending_files = get_files_by_status(db_conn, 'pending')
        assert len(pending_files) == 1
        assert pending_files[0]['file_path'] == sample_file
        
        processed_files = get_files_by_status(db_conn, 'processed')
        assert len(processed_files) == 1
        assert processed_files[0]['file_path'] == path2
    finally:
        if os.path.exists(path2):
            os.remove(path2)
