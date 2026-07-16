import os
import tempfile
import hashlib
import pytest
from pathlib import Path
import yaml

# Import the functions to test
# We assume the test runs from project root or we adjust imports accordingly
# For unit testing isolated functions, we import the logic directly
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from compute_checksum import compute_sha256, ensure_state_file_exists, update_state_file

def test_compute_sha256(tmp_path):
    """Test SHA-256 computation on a known file."""
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_sha256(test_file)

    assert actual_hash == expected_hash

def test_compute_sha256_missing_file():
    """Test that computing checksum on a missing file raises an error."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/path/file.txt"))

def test_ensure_state_file_exists(tmp_path):
    """Test that ensure_state_file_exists creates the file if missing."""
    state_file = tmp_path / "state.yaml"
    ensure_state_file_exists(state_file)
    assert state_file.exists()

def test_update_state_file(tmp_path):
    """Test updating the state file with a checksum."""
    state_file = tmp_path / "state.yaml"
    file_key = "test/file.txt"
    checksum = "abc123"

    update_state_file(state_file, file_key, checksum)

    assert state_file.exists()
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)

    assert "checksums" in state
    assert file_key in state["checksums"]
    assert state["checksums"][file_key]["hash"] == checksum
    assert "timestamp" in state["checksums"][file_key]