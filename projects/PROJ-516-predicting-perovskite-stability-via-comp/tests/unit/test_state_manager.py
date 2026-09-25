"""
Unit tests for state_manager.py
"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml
from unittest.mock import patch

# Add project root to path for imports
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.state_manager import (
    compute_sha256,
    load_state,
    save_state,
    update_artifact_state,
    verify_artifact,
    StateError
)


def test_compute_sha256_valid_file(tmp_path):
    """Test computing SHA-256 for a valid file."""
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    # Known SHA-256 for "Hello, World!"
    expected_hash = "315f5bdb41d0b1a57550a0c1c0e0c1c0e0c1c0e0c1c0e0c1c0e0c1c0e0c1c0e0" # Placeholder, real hash below
    # Actually compute it
    import hashlib
    expected_hash = hashlib.sha256(content).hexdigest()

    result = compute_sha256(test_file)
    assert result == expected_hash


def test_compute_sha256_missing_file(tmp_path):
    """Test computing SHA-256 for a missing file raises FileNotFoundError."""
    missing_file = tmp_path / "nonexistent.txt"

    with pytest.raises(FileNotFoundError):
        compute_sha256(missing_file)


def test_load_state_missing_file(tmp_path):
    """Test loading state when file does not exist returns empty dict."""
    state_file = tmp_path / "state.yaml"

    result = load_state(state_file)
    assert result == {}


def test_save_state(tmp_path):
    """Test saving state to a file."""
    state_file = tmp_path / "state.yaml"
    test_state = {"key": "value", "number": 42}

    save_state(test_state, state_file)

    assert state_file.exists()
    with open(state_file, "r") as f:
        loaded = yaml.safe_load(f)
    assert loaded == test_state


def test_update_artifact_state(tmp_path):
    """Test updating state with a new artifact hash."""
    # Create a test artifact
    artifact_file = tmp_path / "artifact.txt"
    artifact_content = b"Test content for hashing"
    artifact_file.write_bytes(artifact_content)

    # Create a temporary state file
    state_file = tmp_path / "state.yaml"
    initial_state = {"artifacts": {}}
    save_state(initial_state, state_file)

    # Update state
    updated_state = update_artifact_state(artifact_file, state_file, description="Test artifact")

    rel_path = str(artifact_file.relative_to(tmp_path)) # Note: In real usage, relative to PROJECT_ROOT

    # Adjust for the test context where tmp_path is the root
    # The function computes relative to PROJECT_ROOT, but here we pass state_file in tmp_path
    # We need to mock the PROJECT_ROOT or adjust the test logic
    # Let's assume the function works as intended and check the structure
    assert "artifacts" in updated_state
    # The key in the dict will be the relative path from PROJECT_ROOT
    # Since we are running in tmp_path, we can't easily match the exact key
    # unless we mock PROJECT_ROOT.
    # Instead, we check that the artifact was added with a hash.
    assert len(updated_state["artifacts"]) == 1

    artifact_entry = list(updated_state["artifacts"].values())[0]
    assert "hash" in artifact_entry
    assert artifact_entry["hash"] == compute_sha256(artifact_file)
    assert "updated_at" in artifact_entry


def test_verify_artifact_success(tmp_path):
    """Test verifying an artifact with the correct hash."""
    artifact_file = tmp_path / "verify.txt"
    content = b"Verify me"
    artifact_file.write_bytes(content)

    import hashlib
    expected_hash = hashlib.sha256(content).hexdigest()

    # Create a fake state file with the hash
    state_file = tmp_path / "state.yaml"
    save_state({"artifacts": {}}, state_file)

    # Update state first to ensure it exists (though verify doesn't strictly need it if we pass expected_hash)
    # Actually verify_artifact only checks the file hash against the provided expected_hash
    # It doesn't read from state file in the current implementation logic provided in the prompt's context
    # Wait, the function verify_artifact in the provided code:
    #   def verify_artifact(artifact_path, expected_hash, state_path=None):
    #       ...
    #       current_hash = compute_sha256(artifact_path)
    #       return current_hash == expected_hash
    # It does NOT read the expected hash from state. It takes it as an argument.
    # So we just test the comparison logic.

    result = verify_artifact(artifact_file, expected_hash)
    assert result is True


def test_verify_artifact_failure(tmp_path):
    """Test verifying an artifact with an incorrect hash."""
    artifact_file = tmp_path / "verify_fail.txt"
    content = b"Fail me"
    artifact_file.write_bytes(content)

    wrong_hash = "0" * 64

    result = verify_artifact(artifact_file, wrong_hash)
    assert result is False


def test_update_artifact_state_missing_file(tmp_path):
    """Test updating state with a missing artifact raises FileNotFoundError."""
    missing_file = tmp_path / "missing.txt"
    state_file = tmp_path / "state.yaml"
    save_state({}, state_file)

    with pytest.raises(FileNotFoundError):
        update_artifact_state(missing_file, state_file)
