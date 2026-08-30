import os
import hashlib
import yaml
from pathlib import Path
import pytest

# Import the main logic
from update_state_checksum import compute_sha256, update_state_file

@pytest.fixture
def temp_test_files(tmp_path):
    """Create a temporary sample file and state file for testing."""
    # Create a dummy sample file
    sample_file = tmp_path / "era_sample.h5"
    sample_file.write_bytes(b"dummy_era5_sample_data_for_testing")

    # Create a dummy state file
    state_file = tmp_path / "project_state.yaml"
    initial_state = {
        "project_id": "PROJ-TEST",
        "updated_at": "2026-01-01T00:00:00Z",
        "artifact_hashes": {}
    }
    with open(state_file, "w") as f:
        yaml.dump(initial_state, f)

    return sample_file, state_file

def test_compute_sha256(temp_test_files):
    """Test that compute_sha256 returns the correct hash."""
    sample_file, _ = temp_test_files
    expected_hash = hashlib.sha256(sample_file.read_bytes()).hexdigest()
    actual_hash = compute_sha256(str(sample_file))
    assert actual_hash == expected_hash

def test_update_state_file(temp_test_files):
    """Test that update_state_file correctly updates the YAML with the new checksum and timestamp."""
    sample_file, state_file = temp_test_files
    hash_value = compute_sha256(str(sample_file))
    artifact_key = "era5_sample"

    update_state_file(str(state_file), artifact_key, hash_value)

    with open(state_file, "r") as f:
        updated_state = yaml.safe_load(f)

    # Check that the hash was added
    assert "artifact_hashes" in updated_state
    assert artifact_key in updated_state["artifact_hashes"]
    assert updated_state["artifact_hashes"][artifact_key] == hash_value

    # Check that the timestamp was updated
    assert "updated_at" in updated_state
    assert updated_state["updated_at"] != "2026-01-01T00:00:00Z"

def test_main_entry_integration(temp_test_files, caplog):
    """Integration test for the main entry point logic."""
    sample_file, state_file = temp_test_files
    # We can't easily test the CLI main without mocking sys.argv,
    # but we can verify the functions it calls work correctly in sequence.
    hash_val = compute_sha256(str(sample_file))
    update_state_file(str(state_file), "era5_sample", hash_val)

    with open(state_file, "r") as f:
        state = yaml.safe_load(f)

    assert state["artifact_hashes"]["era5_sample"] == hash_val