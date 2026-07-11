"""
Unit tests for src/utils/hash.py
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from utils.hash import (
    compute_file_hash,
    compute_string_hash,
    load_state,
    save_state,
    update_artifact_state,
    verify_artifact,
    get_artifact_hash,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_file(temp_dir):
    """Create a test file with known content."""
    file_path = os.path.join(temp_dir, "test.txt")
    content = "Hello, World!"
    with open(file_path, "w") as f:
        f.write(content)
    return file_path, content


@pytest.fixture
def state_file(temp_dir):
    """Create a temporary state file path."""
    return os.path.join(temp_dir, "state.json")


def test_compute_file_hash(test_file):
    """Test that file hashing produces a consistent SHA-256 hash."""
    file_path, _ = test_file
    hash1 = compute_file_hash(file_path)
    hash2 = compute_file_hash(file_path)

    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1 == hash2
    assert all(c in "0123456789abcdef" for c in hash1)


def test_compute_file_hash_nonexistent():
    """Test that hashing a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash("nonexistent_file.txt")


def test_compute_string_hash():
    """Test string hashing."""
    content = "Test string"
    h1 = compute_string_hash(content)
    h2 = compute_string_hash(content)
    h3 = compute_string_hash(content + " extra")

    assert len(h1) == 64
    assert h1 == h2
    assert h1 != h3


def test_load_state_missing(state_file):
    """Test loading state from a non-existent file returns empty structure."""
    state = load_state(state_file)
    assert state == {"artifacts": {}, "metadata": {"version": 1}}


def test_save_and_load_state(temp_dir, state_file):
    """Test saving and loading state."""
    test_state = {
        "artifacts": {"file.txt": {"hash": "abc123"}},
        "metadata": {"version": 1}
    }
    save_state(test_state, state_file)

    loaded = load_state(state_file)
    assert loaded == test_state


def test_update_artifact_state(test_file, state_file):
    """Test updating the state ledger with a new artifact."""
    file_path, _ = test_file

    # Initial state should be empty
    initial_state = load_state(state_file)
    assert file_path not in initial_state.get("artifacts", {})

    # Update state
    computed_hash = update_artifact_state(file_path, state_file)

    # Verify hash matches file
    assert computed_hash == compute_file_hash(file_path)

    # Verify state was updated
    updated_state = load_state(state_file)
    assert file_path in updated_state["artifacts"]
    assert updated_state["artifacts"][file_path]["hash"] == computed_hash
    assert updated_state["artifacts"][file_path]["algorithm"] == "sha256"


def test_verify_artifact_true(test_file, state_file):
    """Test verify_artifact returns True when hashes match."""
    file_path, _ = test_file
    expected_hash = compute_file_hash(file_path)

    assert verify_artifact(file_path, expected_hash) is True


def test_verify_artifact_false(test_file):
    """Test verify_artifact returns False when hashes don't match."""
    file_path, _ = test_file
    wrong_hash = "a" * 64

    assert verify_artifact(file_path, wrong_hash) is False


def test_get_artifact_hash(test_file, state_file):
    """Test retrieving a stored hash."""
    file_path, _ = test_file

    # Should be None initially
    assert get_artifact_hash(file_path, state_file) is None

    # Update state
    update_artifact_state(file_path, state_file)

    # Should return the hash now
    stored_hash = get_artifact_hash(file_path, state_file)
    assert stored_hash == compute_file_hash(file_path)

    # Non-existent file should return None
    assert get_artifact_hash("nonexistent.txt", state_file) is None