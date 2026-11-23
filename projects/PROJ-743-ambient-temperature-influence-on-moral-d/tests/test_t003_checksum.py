"""
Tests for T003: Checksum ERA5 Sample File.

Verifies that the update_state_checksum logic correctly computes hashes
and updates the state file structure.
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from update_state_checksum import compute_sha256, ensure_state_file_exists, update_state_file, main

@pytest.fixture
def temp_state_dir():
    """Creates a temporary directory for state and data files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_sha256(temp_state_dir):
    """Test SHA-256 computation on a known file."""
    test_file = temp_state_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    expected_hash = hashlib.sha256(test_content).hexdigest()
    actual_hash = compute_sha256(str(test_file))
    
    assert actual_hash == expected_hash, f"Hash mismatch: {actual_hash} != {expected_hash}"

def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.txt")

def test_ensure_state_file_exists_creates_new(temp_state_dir):
    """Test that ensure_state_file_exists creates a new file with correct structure."""
    state_file = temp_state_dir / "state.yaml"
    path = ensure_state_file_exists(str(state_file))
    
    assert path.exists()
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    
    assert "artifact_hashes" in data
    assert data["artifact_hashes"] == {}
    assert "updated_at" in data

def test_update_state_file(temp_state_dir):
    """Test updating the state file with a checksum."""
    state_file = temp_state_dir / "state.yaml"
    # Initialize file first
    ensure_state_file_exists(str(state_file))
    
    test_key = "artifact_hashes.era5_sample"
    test_hash = "abc123def456"
    
    update_state_file(str(state_file), test_key, test_hash)
    
    with open(state_file, "r") as f:
        data = yaml.safe_load(f)
    
    assert "artifact_hashes" in data
    assert "era5_sample" in data["artifact_hashes"]
    assert data["artifact_hashes"]["era5_sample"] == test_hash
    assert "updated_at" in data

def test_main_integration(temp_state_dir):
    """Integration test for the main function."""
    # Create a dummy file
    dummy_file = temp_state_dir / "dummy.h5"
    dummy_file.write_bytes(b"dummy data")
    
    state_file = temp_state_dir / "state.yaml"
    key = "artifact_hashes.test_sample"
    
    # Run main
    main(str(dummy_file), str(state_file), key)
    
    # Verify state file
    with open(state_file, "r") as f:
        data = yaml.safe_load(f)
    
    expected_hash = hashlib.sha256(b"dummy data").hexdigest()
    assert data["artifact_hashes"]["test_sample"] == expected_hash