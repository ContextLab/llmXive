import os
import sys
import tempfile
import hashlib
import yaml
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Adjust path to import the module if running from tests/
# In the actual runner, the module is in code/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from compute_checksum_sample import compute_sha256, ensure_state_file_exists, update_state_file

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    data_raw = tmp_path / "data" / "raw"
    data_raw.mkdir(parents=True)
    state_projects = tmp_path / "state" / "projects"
    state_projects.mkdir(parents=True)
    
    # Create a dummy sample file
    sample_file = data_raw / "era5_sample.h5"
    sample_file.write_bytes(b"dummy_hdf5_content_for_testing")
    
    # Create a dummy state file
    state_file = state_projects / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    initial_state = {
        "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
        "status": "in_progress",
        "artifact_hashes": {},
        "updated_at": "2024-01-01T00:00:00+00:00"
    }
    with open(state_file, "w") as f:
        yaml.dump(initial_state, f)
    
    return {
        "root": tmp_path,
        "sample_file": sample_file,
        "state_file": state_file
    }

def test_compute_sha256(temp_project_dir):
    """Test that compute_sha256 returns the correct hash for a known file."""
    file_path = temp_project_dir["sample_file"]
    expected_hash = hashlib.sha256(b"dummy_hdf5_content_for_testing").hexdigest()
    actual_hash = compute_sha256(file_path)
    assert actual_hash == expected_hash

def test_ensure_state_file_exists_creates_new(temp_project_dir):
    """Test that ensure_state_file_exists creates the file if missing."""
    # Remove the state file
    temp_project_dir["state_file"].unlink()
    
    ensure_state_file_exists(temp_project_dir["state_file"])
    
    assert temp_project_dir["state_file"].exists()
    with open(temp_project_dir["state_file"], "r") as f:
        data = yaml.safe_load(f)
    assert "artifact_hashes" in data
    assert "updated_at" in data

def test_update_state_file(temp_project_dir):
    """Test that update_state_file correctly updates the checksum and timestamp."""
    state_file = temp_project_dir["state_file"]
    checksum = "test_checksum_12345"
    
    update_state_file(state_file, "era5_sample", checksum)
    
    with open(state_file, "r") as f:
        data = yaml.safe_load(f)
    
    assert data["artifact_hashes"]["era5_sample"] == checksum
    assert data["updated_at"] != "2024-01-01T00:00:00+00:00" # Timestamp should be updated
    assert datetime.fromisoformat(data["updated_at"]) > datetime(2024, 1, 1)