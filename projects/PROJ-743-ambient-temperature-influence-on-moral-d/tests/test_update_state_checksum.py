import pytest
from pathlib import Path
import yaml
import os
import tempfile
import shutil

from code.update_state_checksum import compute_sha256, update_state_file

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

def test_compute_sha256(temp_dir):
    """Test that compute_sha256 returns the correct hash for a known file."""
    test_file = temp_dir / "test_file.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
    actual_hash = compute_sha256(test_file)
    
    assert actual_hash == expected_hash

def test_update_state_file_creates_new(temp_dir):
    """Test that update_state_file creates the state file if it doesn't exist."""
    state_file = temp_dir / "state.yaml"
    
    update_state_file(state_file, "test_artifact", "abc123")
    
    assert state_file.exists()
    
    with open(state_file, "r") as f:
        data = yaml.safe_load(f)
    
    assert data["artifact_hashes"]["test_artifact"] == "abc123"
    assert "updated_at" in data
    assert data["updated_at"] is not None

def test_update_state_file_updates_existing(temp_dir):
    """Test that update_state_file updates an existing state file correctly."""
    state_file = temp_dir / "state.yaml"
    
    # Create initial state
    initial_data = {
        "project_id": "TEST-001",
        "artifact_hashes": {"old_artifact": "old_hash"},
        "updated_at": "2023-01-01T00:00:00+00:00"
    }
    with open(state_file, "w") as f:
        yaml.dump(initial_data, f)
    
    # Update with new artifact
    update_state_file(state_file, "new_artifact", "new_hash")
    
    with open(state_file, "r") as f:
        data = yaml.safe_load(f)
    
    assert data["artifact_hashes"]["old_artifact"] == "old_hash"
    assert data["artifact_hashes"]["new_artifact"] == "new_hash"
    # Verify timestamp was updated (it should be different from initial)
    assert data["updated_at"] != "2023-01-01T00:00:00+00:00"
    assert "2023" in data["updated_at"] # Basic check that it's a recent-ish date string format