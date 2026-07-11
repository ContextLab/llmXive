"""
Tests for Constitution Principle V: State Update Utility.
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path
import sys

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from update_state import calculate_file_hash, update_state_yaml, verify_artifact_integrity

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_artifact(temp_dir):
    """Create a sample artifact file."""
    artifact_path = temp_dir / "test_artifact.txt"
    content = "This is a test artifact for hashing."
    artifact_path.write_text(content)
    return str(artifact_path)

@pytest.fixture
def state_file(temp_dir):
    """Create an empty state file."""
    state_path = temp_dir / "state.yaml"
    state_path.write_text("{}")
    return str(state_path)

def test_calculate_file_hash(sample_artifact):
    """Test that file hash is calculated correctly and consistently."""
    hash1 = calculate_file_hash(sample_artifact)
    hash2 = calculate_file_hash(sample_artifact)
    
    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1 == hash2  # Consistent hashing
    assert hash1.islower()  # Hex digest is lowercase

def test_calculate_file_hash_nonexistent():
    """Test that hashing a nonexistent file raises an error."""
    with pytest.raises(FileNotFoundError):
        calculate_file_hash("nonexistent_file.txt")

def test_update_state_yaml(temp_dir, sample_artifact, state_file):
    """Test updating state.yaml with a new artifact."""
    description = "Test artifact description"
    
    update_state_yaml(state_file, sample_artifact, description)
    
    # Verify state file was updated
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    # Find the artifact in state (path might be relative or absolute)
    artifact_key = None
    for key in state.keys():
        if "test_artifact.txt" in key:
            artifact_key = key
            break
    
    assert artifact_key is not None, "Artifact not found in state"
    assert state[artifact_key]["description"] == description
    assert "hash" in state[artifact_key]
    assert len(state[artifact_key]["hash"]) == 64
    assert "updated_at" in state[artifact_key]

def test_update_state_yaml_existing(temp_dir, sample_artifact, state_file):
    """Test updating state.yaml when artifact already exists."""
    description1 = "First description"
    description2 = "Updated description"
    
    update_state_yaml(state_file, sample_artifact, description1)
    update_state_yaml(state_file, sample_artifact, description2)
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    artifact_key = None
    for key in state.keys():
        if "test_artifact.txt" in key:
            artifact_key = key
            break
    
    assert state[artifact_key]["description"] == description2

def test_verify_artifact_integrity_success(temp_dir, sample_artifact, state_file):
    """Test successful integrity verification."""
    update_state_yaml(state_file, sample_artifact, "Test artifact")
    
    is_valid = verify_artifact_integrity(state_file, sample_artifact)
    assert is_valid is True

def test_verify_artifact_integrity_failure(temp_dir, sample_artifact, state_file):
    """Test failed integrity verification when file is modified."""
    update_state_yaml(state_file, sample_artifact, "Test artifact")
    
    # Modify the artifact
    Path(sample_artifact).write_text("Modified content")
    
    is_valid = verify_artifact_integrity(state_file, sample_artifact)
    assert is_valid is False

def test_verify_artifact_integrity_missing_state(temp_dir, sample_artifact):
    """Test verification when state file doesn't exist."""
    is_valid = verify_artifact_integrity("nonexistent_state.yaml", sample_artifact)
    assert is_valid is False

def test_verify_artifact_integrity_missing_artifact(temp_dir, state_file):
    """Test verification when artifact doesn't exist."""
    is_valid = verify_artifact_integrity(state_file, "nonexistent_artifact.txt")
    assert is_valid is False

def test_update_state_yaml_creates_directory(temp_dir, sample_artifact):
    """Test that update_state_yaml creates the directory for state file if needed."""
    nested_state = temp_dir / "nested" / "subdir" / "state.yaml"
    
    update_state_yaml(str(nested_state), sample_artifact, "Test")
    
    assert nested_state.exists()
    with open(nested_state, 'r') as f:
        state = yaml.safe_load(f)
    assert len(state) > 0
