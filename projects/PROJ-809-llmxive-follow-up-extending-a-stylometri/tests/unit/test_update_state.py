"""
Unit tests for update_state.py

These tests verify the artifact hashing and state management functionality
of the update_state module.
"""

import os
import tempfile
import yaml
from pathlib import Path
import pytest

# Add project root to path if running from tests/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.update_state import (
    load_state,
    save_state,
    register_artifact,
    update_artifact_hash,
    verify_artifact_integrity,
    get_artifact_metadata,
    list_artifacts,
    hash_artifact
)


@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state and artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_artifact(temp_state_dir):
    """Create a sample artifact file."""
    artifact_path = Path(temp_state_dir) / "test_artifact.txt"
    with open(artifact_path, "w") as f:
        f.write("This is a test artifact content.")
    return str(artifact_path)


@pytest.fixture
def sample_state(temp_state_dir, sample_artifact):
    """Create a sample state file with one artifact."""
    state_path = Path(temp_state_dir) / "test_state.yaml"
    state = {
        "project_id": "TEST-001",
        "artifacts": {
            "test_artifact.txt": {
                "path": "test_artifact.txt",
                "hash": hash_artifact(sample_artifact),
                "type": "test",
                "registered_at": "2023-01-01T00:00:00"
            }
        }
    }
    with open(state_path, "w") as f:
        yaml.dump(state, f)
    return str(state_path)


def test_hash_artifact(sample_artifact):
    """Test that hash_artifact computes a valid SHA-256 hash."""
    hash_val = hash_artifact(sample_artifact)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert all(c in "0123456789abcdef" for c in hash_val)


def test_hash_artifact_not_found():
    """Test that hash_artifact raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        hash_artifact("nonexistent_file.txt")


def test_load_state_nonexistent(temp_state_dir):
    """Test loading a non-existent state file returns a default structure."""
    state_path = Path(temp_state_dir) / "nonexistent.yaml"
    state = load_state(str(state_path))
    assert "artifacts" in state
    assert "project_id" in state
    assert state["artifacts"] == {}


def test_load_state_existing(sample_state):
    """Test loading an existing state file."""
    state = load_state(sample_state)
    assert "test_artifact.txt" in state["artifacts"]
    assert state["artifacts"]["test_artifact.txt"]["type"] == "test"


def test_save_state(temp_state_dir):
    """Test saving a state dictionary."""
    state_path = Path(temp_state_dir) / "new_state.yaml"
    test_state = {
        "project_id": "TEST-002",
        "artifacts": {
            "new_artifact.txt": {
                "path": "new_artifact.txt",
                "hash": "abc123",
                "type": "test"
            }
        }
    }
    save_state(test_state, str(state_path))
    assert state_path.exists()

    # Verify content
    with open(state_path, "r") as f:
        loaded = yaml.safe_load(f)
    assert loaded["project_id"] == "TEST-002"
    assert "new_artifact.txt" in loaded["artifacts"]


def test_register_artifact(temp_state_dir, sample_artifact):
    """Test registering a new artifact."""
    state_path = Path(temp_state_dir) / "state.yaml"
    artifact_path = str(Path(sample_artifact).relative_to(temp_state_dir))

    state = register_artifact(
        artifact_path,
        "test_type",
        "Test description",
        ["tag1", "tag2"],
        str(state_path)
    )

    assert artifact_path in state["artifacts"]
    assert state["artifacts"][artifact_path]["type"] == "test_type"
    assert state["artifacts"][artifact_path]["description"] == "Test description"
    assert set(state["artifacts"][artifact_path]["tags"]) == {"tag1", "tag2"}

    # Verify hash is correct
    expected_hash = hash_artifact(sample_artifact)
    assert state["artifacts"][artifact_path]["hash"] == expected_hash


def test_update_artifact_hash(temp_state_dir, sample_state, sample_artifact):
    """Test updating an artifact's hash."""
    # Modify the artifact
    with open(sample_artifact, "a") as f:
        f.write(" Modified content.")

    state = update_artifact_hash("test_artifact.txt", sample_state)
    new_hash = state["artifacts"]["test_artifact.txt"]["hash"]

    # Verify hash changed
    assert new_hash != hash_artifact(sample_artifact, sample_state)  # This will fail if we don't recompute
    # Recompute expected hash
    expected_hash = hash_artifact(sample_artifact)
    assert new_hash == expected_hash


def test_verify_artifact_integrity_valid(sample_state, sample_artifact):
    """Test verifying integrity of a valid artifact."""
    is_valid = verify_artifact_integrity("test_artifact.txt", sample_state)
    assert is_valid is True


def test_verify_artifact_integrity_invalid(temp_state_dir, sample_state, sample_artifact):
    """Test verifying integrity of a modified artifact."""
    # Modify the artifact
    with open(sample_artifact, "a") as f:
        f.write(" Modified.")

    is_valid = verify_artifact_integrity("test_artifact.txt", sample_state)
    assert is_valid is False


def test_get_artifact_metadata(sample_state):
    """Test retrieving artifact metadata."""
    meta = get_artifact_metadata("test_artifact.txt", sample_state)
    assert meta is not None
    assert meta["type"] == "test"
    assert meta["path"] == "test_artifact.txt"


def test_get_artifact_metadata_not_found(sample_state):
    """Test retrieving metadata for a non-existent artifact."""
    meta = get_artifact_metadata("nonexistent.txt", sample_state)
    assert meta is None


def test_list_artifacts_all(sample_state):
    """Test listing all artifacts."""
    artifacts = list_artifacts(state_file=sample_state)
    assert len(artifacts) == 1
    assert artifacts[0]["path"] == "test_artifact.txt"


def test_list_artifacts_filtered(sample_state):
    """Test listing artifacts filtered by type."""
    # Add another artifact of different type
    state = load_state(sample_state)
    state["artifacts"]["other.txt"] = {
        "path": "other.txt",
        "hash": "xyz789",
        "type": "other_type"
    }
    save_state(state, sample_state)

    # Filter by type
    artifacts = list_artifacts(artifact_type="test", state_file=sample_state)
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "test"