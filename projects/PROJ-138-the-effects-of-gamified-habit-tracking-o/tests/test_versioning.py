"""
Tests for the versioning module (T008).
"""
import os
import tempfile
import hashlib
import yaml
import pytest
from pathlib import Path

# Import the module under test
from code.utils.versioning import (
    calculate_sha256,
    load_state,
    save_state,
    update_artifact_state,
    verify_artifacts,
    STATE_FILE
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield tmpdir
        os.chdir(original_cwd)

@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for hashing."""
    file_path = os.path.join(temp_dir, "test_sample.txt")
    content = "This is a test artifact content."
    with open(file_path, "w") as f:
        f.write(content)
    return file_path

def test_calculate_sha256(sample_file):
    """Test SHA-256 calculation."""
    # Calculate expected hash manually
    sha256_hash = hashlib.sha256()
    with open(sample_file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    expected_hash = sha256_hash.hexdigest()
    
    # Test function output
    result = calculate_sha256(sample_file)
    
    assert result == expected_hash
    assert len(result) == 64  # SHA-256 hex length

def test_calculate_sha256_nonexistent_file(temp_dir):
    """Test SHA-256 calculation on non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256(os.path.join(temp_dir, "nonexistent.txt"))

def test_load_state_empty(temp_dir):
    """Test loading state when state.yaml does not exist."""
    state = load_state()
    assert state == {"artifacts": {}}

def test_save_state_and_load(temp_dir):
    """Test saving and loading state."""
    test_state = {
        "artifacts": {
            "data/test.csv": {
                "hash": "abc123",
                "description": "Test artifact",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    }
    
    save_state(test_state)
    
    assert os.path.exists(STATE_FILE)
    
    loaded_state = load_state()
    assert loaded_state == test_state

def test_update_artifact_state(sample_file):
    """Test updating artifact state."""
    # Ensure state file doesn't exist initially
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    
    update_artifact_state(sample_file, "Test description")
    
    assert os.path.exists(STATE_FILE)
    
    state = load_state()
    assert sample_file in state["artifacts"]
    assert "hash" in state["artifacts"][sample_file]
    assert state["artifacts"][sample_file]["description"] == "Test description"
    assert "updated_at" in state["artifacts"][sample_file]

def test_update_artifact_state_nonexistent(temp_dir):
    """Test updating state for non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        update_artifact_state(os.path.join(temp_dir, "missing.txt"))

def test_verify_artifacts_match(temp_dir):
    """Test verification when hashes match."""
    # Create a file and update state
    file_path = os.path.join(temp_dir, "verify_test.txt")
    with open(file_path, "w") as f:
        f.write("Content for verification")
    
    update_artifact_state(file_path)
    
    # Verify with correct hash
    expected_hashes = {file_path: load_state()["artifacts"][file_path]["hash"]}
    assert verify_artifacts(expected_hashes) is True

def test_verify_artifacts_mismatch(temp_dir):
    """Test verification when hashes do not match."""
    file_path = os.path.join(temp_dir, "mismatch_test.txt")
    with open(file_path, "w") as f:
        f.write("Content")
    
    update_artifact_state(file_path)
    
    # Verify with wrong hash
    wrong_hashes = {file_path: "wrong_hash_value"}
    assert verify_artifacts(wrong_hashes) is False

def test_verify_artifacts_missing(temp_dir):
    """Test verification when artifact is missing from state."""
    file_path = os.path.join(temp_dir, "missing_state_test.txt")
    with open(file_path, "w") as f:
        f.write("Content")
    
    # Don't update state, just try to verify
    assert verify_artifacts({file_path: "some_hash"}) is False
