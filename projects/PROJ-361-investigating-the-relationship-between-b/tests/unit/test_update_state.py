"""
Unit tests for code.utils.update_state module.
"""
import pytest
import os
import tempfile
from pathlib import Path
import hashlib
import json
from datetime import datetime

# Import the module under test
from code.utils.update_state import (
    calculate_file_hash,
    get_file_metadata,
    register_artifact,
    update_artifact_status,
    verify_artifact_integrity,
    get_pipeline_state,
    STATUS_RAW,
    STATUS_PROCESSED
)

# Import DB setup helper to ensure clean state for tests
from code.utils.db_schema import init_db, get_schema, get_files_by_status

@pytest.fixture
def temp_db_path():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    yield path
    if path.exists():
        os.unlink(path)

@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        path = Path(f.name)
    yield path
    if path.exists():
        os.unlink(path)

@pytest.fixture
def large_temp_file():
    """Create a larger temporary file to test chunked reading."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
        # Write 1MB of data
        f.write(b'x' * (1024 * 1024))
        path = Path(f.name)
    yield path
    if path.exists():
        os.unlink(path)

def test_calculate_file_hash(temp_file):
    """Test SHA-256 calculation on a small file."""
    expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
    result = calculate_file_hash(temp_file)
    assert result == expected_hash
    assert len(result) == 64  # SHA-256 hex length

def test_calculate_file_hash_large_file(large_temp_file):
    """Test SHA-256 calculation on a larger file (chunked read)."""
    expected_hash = hashlib.sha256(b'x' * (1024 * 1024)).hexdigest()
    result = calculate_file_hash(large_temp_file)
    assert result == expected_hash

def test_calculate_file_hash_missing_file(temp_db_path):
    """Test that FileNotFoundError is raised for missing file."""
    missing_path = Path("/nonexistent/file.txt")
    with pytest.raises(FileNotFoundError):
        calculate_file_hash(missing_path)

def test_get_file_metadata(temp_file):
    """Test metadata extraction."""
    meta = get_file_metadata(temp_file)
    assert meta['path'] == str(temp_file)
    assert meta['size_bytes'] == 13  # "Hello, World!"
    assert 'hash' in meta
    assert 'modified_at' in meta
    assert 'created_at' in meta

def test_register_artifact(temp_db_path, temp_file):
    """Test registering a new artifact."""
    subject_id = "sub-001"
    register_artifact(subject_id, temp_file, STATUS_RAW, temp_db_path)
    
    # Verify in DB
    files = get_files_by_status(temp_db_path, subject_id, status=None)
    assert len(files) == 1
    assert files[0]['file_path'] == str(temp_file)
    assert files[0]['status'] == STATUS_RAW
    assert files[0]['checksum'] == calculate_file_hash(temp_file)

def test_register_artifact_missing_file(temp_db_path):
    """Test that registering a missing file raises FileNotFoundError."""
    missing_path = Path("/nonexistent/file.txt")
    with pytest.raises(FileNotFoundError):
        register_artifact("sub-001", missing_path, STATUS_RAW, temp_db_path)

def test_update_artifact_status(temp_db_path, temp_file):
    """Test updating artifact status."""
    subject_id = "sub-001"
    register_artifact(subject_id, temp_file, STATUS_RAW, temp_db_path)
    
    update_artifact_status(subject_id, temp_file, STATUS_PROCESSED, temp_db_path)
    
    files = get_files_by_status(temp_db_path, subject_id, status=None)
    assert files[0]['status'] == STATUS_PROCESSED

def test_update_artifact_status_unregistered(temp_db_path, temp_file):
    """Test updating status of an unregistered file raises ValueError."""
    subject_id = "sub-001"
    with pytest.raises(ValueError):
        update_artifact_status(subject_id, temp_file, STATUS_PROCESSED, temp_db_path)

def test_verify_artifact_integrity_success(temp_db_path, temp_file):
    """Test successful integrity verification."""
    subject_id = "sub-001"
    register_artifact(subject_id, temp_file, STATUS_RAW, temp_db_path)
    
    assert verify_artifact_integrity(subject_id, temp_file, temp_db_path)

def test_verify_artifact_integrity_failure(temp_db_path, temp_file):
    """Test integrity verification failure after file modification."""
    subject_id = "sub-001"
    register_artifact(subject_id, temp_file, STATUS_RAW, temp_db_path)
    
    # Modify the file
    with open(temp_file, 'w') as f:
        f.write("Modified Content")
        
    assert not verify_artifact_integrity(subject_id, temp_file, temp_db_path)

def test_get_pipeline_state(temp_db_path, temp_file):
    """Test getting pipeline state for a subject."""
    subject_id = "sub-001"
    register_artifact(subject_id, temp_file, STATUS_RAW, temp_db_path)
    
    state = get_pipeline_state(subject_id, temp_db_path)
    assert str(temp_file) in state
    assert state[str(temp_file)] == STATUS_RAW
