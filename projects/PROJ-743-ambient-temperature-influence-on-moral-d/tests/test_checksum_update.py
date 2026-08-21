import os
import tempfile
import hashlib
from pathlib import Path
import yaml

import pytest

from update_state_checksum import compute_sha256, update_state_file, main


def test_compute_sha256():
    """Test that compute_sha256 returns the correct hash for a known file."""
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = b"Hello, World!"
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Compute expected hash manually
        expected_hash = hashlib.sha256(content).hexdigest()

        # Compute hash using the function
        actual_hash = compute_sha256(tmp_path)

        assert actual_hash == expected_hash, f"Expected {expected_hash}, got {actual_hash}"
    finally:
        os.unlink(tmp_path)


def test_update_state_file():
    """Test that update_state_file correctly updates a nested key and timestamp."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"

        # Create initial state
        initial_data = {
            "project_id": "PROJ-743",
            "artifact_hashes": {
                "existing_file": "abc123"
            },
            "updated_at": "2023-01-01T00:00:00+00:00"
        }

        with open(state_file, "w") as f:
            yaml.dump(initial_data, f)

        # Update the state
        update_state_file(str(state_file), "artifact_hashes.new_file", "xyz789")

        # Read back and verify
        with open(state_file, "r") as f:
            updated_data = yaml.safe_load(f)

        assert updated_data["artifact_hashes"]["new_file"] == "xyz789"
        assert updated_data["artifact_hashes"]["existing_file"] == "abc123"
        # Verify timestamp was updated
        assert updated_data["updated_at"] != "2023-01-01T00:00:00+00:00"
        # Verify the new timestamp is in ISO format
        assert "T" in updated_data["updated_at"]


def test_main_function():
    """Test the main function end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy data file
        data_file = Path(tmpdir) / "data.h5"
        data_content = b"dummy data for checksum"
        data_file.write_bytes(data_content)

        # Create a dummy state file
        state_file = Path(tmpdir) / "state.yaml"
        state_file.write_text("updated_at: 2023-01-01T00:00:00+00:00\n")

        # Run main
        main(str(data_file), str(state_file), "artifact_hashes.test_file")

        # Verify state file was updated
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f)

        expected_hash = hashlib.sha256(data_content).hexdigest()
        assert state_data["artifact_hashes"]["test_file"] == expected_hash
        assert state_data["updated_at"] != "2023-01-01T00:00:00+00:00"
