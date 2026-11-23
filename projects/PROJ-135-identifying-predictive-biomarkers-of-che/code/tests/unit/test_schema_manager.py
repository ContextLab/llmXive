import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.schema_manager import compute_sha256, update_state_with_schema_checksums


def test_compute_sha256():
    """Test SHA256 computation on a temporary file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        checksum = compute_sha256(temp_path)
        expected = hashlib.sha256(b"test content").hexdigest()
        assert checksum == expected, f"Checksum mismatch: {checksum} != {expected}"
    finally:
        os.unlink(temp_path)

def test_update_state_with_schema_checksums():
    """Test updating state file with checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        checksums = {"schema1.yaml": "abc123", "schema2.yaml": "def456"}

        update_state_with_schema_checksums(checksums, state_file)

        assert state_file.exists()
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f)

        assert "artifact_hashes" in state_data
        assert state_data["artifact_hashes"]["schema1.yaml"] == "abc123"
        assert state_data["artifact_hashes"]["schema2.yaml"] == "def456"

def test_update_state_with_existing_data():
    """Test updating state file when it already exists with data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        # Create initial state
        initial_data = {"existing_key": "existing_value"}
        with open(state_file, "w") as f:
            yaml.dump(initial_data, f)

        checksums = {"schema1.yaml": "abc123"}
        update_state_with_schema_checksums(checksums, state_file)

        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f)

        assert state_data["existing_key"] == "existing_value"
        assert state_data["artifact_hashes"]["schema1.yaml"] == "abc123"