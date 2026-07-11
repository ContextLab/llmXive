"""
test_update_state.py - Unit tests for update_state module
"""

import os
import tempfile
import yaml
import pytest
from pathlib import Path
import sys
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.update_state import (
    calculate_file_hash,
    load_state_yaml,
    save_state_yaml,
    update_state_yaml,
    verify_artifact_integrity,
    DEFAULT_STATE_FILE
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_artifact(temp_dir):
    """Create a sample artifact file."""
    artifact_path = temp_dir / "test_artifact.txt"
    content = "This is a test artifact for hashing and state management."
    artifact_path.write_text(content)
    return artifact_path


@pytest.fixture
def state_file(temp_dir):
    """Create a temporary state file path."""
    return temp_dir / "state.yaml"


def test_calculate_file_hash(sample_artifact):
    """Test file hash calculation."""
    # Calculate hash
    file_hash = calculate_file_hash(sample_artifact)

    # Verify it's a valid hex string
    assert len(file_hash) == 64, "SHA256 hash should be 64 characters"
    assert all(c in '0123456789abcdef' for c in file_hash), "Hash should be hexadecimal"

    # Verify hash matches content
    expected_hash = hashlib.sha256(sample_artifact.read_bytes()).hexdigest()
    assert file_hash == expected_hash, "Calculated hash should match expected hash"


def test_calculate_file_hash_nonexistent():
    """Test hash calculation on non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_file_hash(Path("/nonexistent/file.txt"))


def test_update_state_yaml(sample_artifact, state_file):
    """Test updating state with a new artifact."""
    # Update state
    state = update_state_yaml(sample_artifact, state_file)

    # Verify state structure
    assert "artifacts" in state
    assert "version" in state
    assert "last_updated" in state

    # Verify artifact entry
    artifact_key = str(sample_artifact.relative_to(Path.cwd()))
    assert artifact_key in state["artifacts"]

    entry = state["artifacts"][artifact_key]
    assert "hash" in entry
    assert "path" in entry
    assert "size_bytes" in entry
    assert "algorithm" in entry
    assert entry["algorithm"] == "sha256"

    # Verify hash is correct
    expected_hash = hashlib.sha256(sample_artifact.read_bytes()).hexdigest()
    assert entry["hash"] == expected_hash


def test_update_state_yaml_existing(sample_artifact, state_file):
    """Test updating state with an existing artifact (should update hash)."""
    # First update
    state1 = update_state_yaml(sample_artifact, state_file)
    hash1 = state1["artifacts"][str(sample_artifact.relative_to(Path.cwd()))]["hash"]

    # Modify artifact
    sample_artifact.write_text("Modified content")

    # Second update
    state2 = update_state_yaml(sample_artifact, state_file)
    hash2 = state2["artifacts"][str(sample_artifact.relative_to(Path.cwd()))]["hash"]

    # Hashes should be different
    assert hash1 != hash2, "Hash should change when file content changes"

    # Verify new hash is correct
    expected_hash = hashlib.sha256(sample_artifact.read_bytes()).hexdigest()
    assert hash2 == expected_hash


def test_verify_artifact_integrity_success(sample_artifact, state_file):
    """Test successful artifact verification."""
    # Add artifact to state
    update_state_yaml(sample_artifact, state_file)

    # Verify
    is_valid = verify_artifact_integrity(sample_artifact, state_file)
    assert is_valid, "Artifact should be valid"


def test_verify_artifact_integrity_failure(sample_artifact, state_file):
    """Test failed artifact verification (modified file)."""
    # Add artifact to state
    update_state_yaml(sample_artifact, state_file)

    # Modify file
    sample_artifact.write_text("Modified content")

    # Verify should fail
    is_valid = verify_artifact_integrity(sample_artifact, state_file, strict=False)
    assert not is_valid, "Artifact should be invalid after modification"


def test_verify_artifact_integrity_missing_state(sample_artifact, state_file):
    """Test verification with missing state file."""
    # Don't create state file
    is_valid = verify_artifact_integrity(sample_artifact, state_file, strict=False)
    assert not is_valid, "Should return False when state file is missing"

    with pytest.raises(FileNotFoundError):
        verify_artifact_integrity(sample_artifact, state_file, strict=True)


def test_verify_artifact_integrity_missing_artifact(state_file):
    """Test verification with missing artifact file."""
    # Create state file
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("artifacts: {}\n")

    non_existent = Path("/nonexistent/artifact.txt")
    is_valid = verify_artifact_integrity(non_existent, state_file, strict=False)
    assert not is_valid, "Should return False when artifact is missing"

    with pytest.raises(FileNotFoundError):
        verify_artifact_integrity(non_existent, state_file, strict=True)


def test_update_state_yaml_creates_directory(temp_dir):
    """Test that update_state_yaml creates the directory if it doesn't exist."""
    nested_path = temp_dir / "nested" / "deep" / "state.yaml"
    sample_file = temp_dir / "artifact.txt"
    sample_file.write_text("test")

    # This should create the nested directory
    state = update_state_yaml(sample_file, nested_path)

    assert nested_path.exists(), "Directory should be created"
    assert state is not None, "State should be returned"


def test_save_and_load_state_yaml(temp_dir):
    """Test saving and loading state YAML."""
    state_file = temp_dir / "test_state.yaml"
    test_state = {
        "version": "1.0",
        "artifacts": {
            "test.txt": {
                "hash": "abc123",
                "path": "/test.txt"
            }
        },
        "last_updated": 1234567890
    }

    # Save
    save_state_yaml(test_state, state_file)
    assert state_file.exists(), "State file should be created"

    # Load
    loaded_state = load_state_yaml(state_file)
    assert loaded_state == test_state, "Loaded state should match saved state"


def test_load_state_yaml_creates_default(temp_dir):
    """Test that load_state_yaml creates a default state if file doesn't exist."""
    state_file = temp_dir / "new_state.yaml"

    state = load_state_yaml(state_file)

    assert state_file.exists(), "State file should be created"
    assert "version" in state
    assert "artifacts" in state
    assert isinstance(state["artifacts"], dict)