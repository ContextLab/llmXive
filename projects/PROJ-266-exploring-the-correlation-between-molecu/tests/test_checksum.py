"""
Unit tests for the checksum utility.
"""
import os
import tempfile
from pathlib import Path
import pytest
import hashlib

# Import the module under test
from utils.checksum import (
    compute_file_checksum,
    register_checksum,
    verify_checksum,
    scan_and_register_data_files,
    load_state_file,
    save_state_file
)
from utils.config import get_project_root

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content for checksum verification")
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_state_file():
    """Create a temporary state file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        f.write("id: test-state\nchecksums: {}\n")
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

def test_compute_file_checksum(temp_file):
    """Test that compute_file_checksum returns the correct SHA-256 hash."""
    expected_hash = hashlib.sha256(b"test content for checksum verification").hexdigest()
    actual_hash = compute_file_checksum(temp_file)
    assert actual_hash == expected_hash
    assert len(actual_hash) == 64  # SHA-256 produces 64 hex characters

def test_compute_file_checksum_file_not_found():
    """Test that compute_file_checksum raises FileNotFoundError for missing files."""
    non_existent = Path("/non/existent/file.txt")
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(non_existent)

def test_compute_file_checksum_unsupported_algorithm(temp_file):
    """Test that compute_file_checksum raises ValueError for unsupported algorithms."""
    with pytest.raises(ValueError):
        compute_file_checksum(temp_file, algorithm="md5")

def test_register_checksum():
    """Test that register_checksum updates the state dictionary correctly."""
    state = {}
    file_path = Path("data/test.csv")
    checksum = "abc123"
    
    updated_state = register_checksum(file_path, state, checksum)
    
    assert 'checksums' in updated_state
    assert str(file_path) in updated_state['checksums']
    assert updated_state['checksums'][str(file_path)]['hash'] == checksum
    assert updated_state['checksums'][str(file_path)]['algorithm'] == 'sha256'

def test_verify_checksum_success(temp_file):
    """Test verify_checksum returns True when checksums match."""
    expected_hash = compute_file_checksum(temp_file)
    assert verify_checksum(temp_file, expected_hash) is True

def test_verify_checksum_failure(temp_file):
    """Test verify_checksum returns False when checksums don't match."""
    assert verify_checksum(temp_file, "wrong_hash") is False

def test_load_state_file(temp_state_file):
    """Test that load_state_file correctly loads YAML content."""
    state = load_state_file(temp_state_file)
    assert state['id'] == 'test-state'
    assert 'checksums' in state

def test_save_state_file(temp_state_file):
    """Test that save_state_file correctly writes YAML content."""
    state = {
        'id': 'new-state',
        'checksums': {
            'data/test.csv': {
                'algorithm': 'sha256',
                'hash': 'abc123'
            }
        }
    }
    save_state_file(state, temp_state_file)
    
    # Verify the file was written correctly
    loaded_state = load_state_file(temp_state_file)
    assert loaded_state['id'] == 'new-state'
    assert 'data/test.csv' in loaded_state['checksums']