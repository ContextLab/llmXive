"""
Unit tests for the provenance tracking module.

Tests checksum generation, recording, and verification functionality.
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import the module under test
from utils.provenance import (
    ensure_state_directory,
    get_provenance_state_file,
    compute_file_checksum,
    load_existing_state,
    save_state,
    record_artifact,
    verify_artifact,
    list_artifacts
)

@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary state directory for testing."""
    # Monkey-patch the state directory for testing
    import utils.provenance as prov_module
    original_state_dir = prov_module.STATE_DIR
    prov_module.STATE_DIR = tmp_path / "state" / "projects"
    yield tmp_path
    # Restore original
    prov_module.STATE_DIR = original_state_dir

@pytest.fixture
def temp_artifact(tmp_path):
    """Create a temporary artifact file for testing."""
    artifact_path = tmp_path / "test_artifact.txt"
    artifact_path.write_text("test content for provenance verification")
    return artifact_path

def test_ensure_state_directory(temp_state_dir):
    """Test that the state directory is created if it doesn't exist."""
    result = ensure_state_directory()
    assert result.exists()
    assert result.is_dir()

def test_get_provenance_state_file(temp_state_dir):
    """Test that the state file path is correctly generated."""
    result = get_provenance_state_file()
    assert result.parent.exists()
    assert result.name.endswith(".yaml")

def test_compute_file_checksum(temp_artifact):
    """Test checksum computation for a file."""
    checksum = compute_file_checksum(temp_artifact)
    assert len(checksum) == 64  # SHA256 produces 64 hex characters
    assert all(c in "0123456789abcdef" for c in checksum)

def test_compute_file_checksum_nonexistent():
    """Test that FileNotFoundError is raised for nonexistent files."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("nonexistent_file.txt"))

def test_load_existing_state_new(temp_state_dir):
    """Test loading state when no state file exists."""
    state = load_existing_state()
    assert "project_id" in state
    assert "created_at" in state
    assert "artifacts" in state
    assert isinstance(state["artifacts"], dict)

def test_save_state(temp_state_dir):
    """Test saving state to disk."""
    test_state = {
        "project_id": "TEST-001",
        "created_at": "2023-01-01T00:00:00",
        "artifacts": {"test": {"path": "test.txt"}}
    }
    save_state(test_state)
    
    state_file = get_provenance_state_file()
    assert state_file.exists()
    
    with open(state_file, "r") as f:
        loaded_state = yaml.safe_load(f)
        
    assert loaded_state == test_state

def test_record_artifact(temp_state_dir, temp_artifact):
    """Test recording an artifact to the state file."""
    # Record the artifact
    record = record_artifact(
        temp_artifact,
        artifact_type="test",
        description="Test artifact"
    )
    
    # Verify the record structure
    assert "path" in record
    assert "type" in record
    assert "checksum" in record
    assert "recorded_at" in record
    assert record["type"] == "test"
    assert record["description"] == "Test artifact"
    
    # Verify the state file was updated
    state = load_existing_state()
    assert str(temp_artifact) in state["artifacts"]

def test_record_artifact_nonexistent():
    """Test that FileNotFoundError is raised for nonexistent artifacts."""
    with pytest.raises(FileNotFoundError):
        record_artifact(
            Path("nonexistent.txt"),
            artifact_type="test"
        )

def test_verify_artifact_success(temp_state_dir, temp_artifact):
    """Test successful artifact verification."""
    # Record the artifact first
    record_artifact(temp_artifact, artifact_type="test")
    
    # Verify it
    assert verify_artifact(temp_artifact) is True

def test_verify_artifact_failure(temp_state_dir, temp_artifact):
    """Test artifact verification after modification."""
    # Record the artifact
    record_artifact(temp_artifact, artifact_type="test")
    
    # Modify the artifact
    temp_artifact.write_text("modified content")
    
    # Verify should fail
    assert verify_artifact(temp_artifact) is False

def test_verify_artifact_unrecorded(temp_state_dir, temp_artifact):
    """Test verification of an unrecorded artifact."""
    assert verify_artifact(temp_artifact) is False

def test_list_artifacts(temp_state_dir, temp_artifact):
    """Test listing artifacts."""
    # Record multiple artifacts
    record_artifact(temp_artifact, artifact_type="data")
    
    # Create another artifact
    temp_artifact2 = temp_artifact.parent / "test2.txt"
    temp_artifact2.write_text("test content 2")
    record_artifact(temp_artifact2, artifact_type="model")
    
    # List all artifacts
    all_artifacts = list_artifacts()
    assert len(all_artifacts) == 2
    
    # Filter by type
    data_artifacts = list_artifacts(artifact_type="data")
    assert len(data_artifacts) == 1
    assert data_artifacts[0]["type"] == "data"
    
    model_artifacts = list_artifacts(artifact_type="model")
    assert len(model_artifacts) == 1
    assert model_artifacts[0]["type"] == "model"