"""
Unit tests for the artifact versioning utility.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from utils.versioning import (
    load_state_file,
    compute_artifact_checksums,
    update_state_file,
    get_state_file_path,
    record_data_generation_state
)
from utils.hash_artifacts import calculate_sha256

@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory for testing state files."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    return projects_dir

@pytest.fixture
def sample_artifact(tmp_path):
    """Create a sample artifact file for testing."""
    artifact = tmp_path / "test_artifact.txt"
    artifact.write_text("test content for checksum")
    return artifact

def test_load_state_file_existing(temp_state_dir):
    """Test loading an existing state file."""
    state_file = temp_state_dir / "test_project.yaml"
    initial_state = {
        "project_id": "TEST-001",
        "state": "initializing",
        "artifacts": {}
    }
    with open(state_file, 'w') as f:
        yaml.dump(initial_state, f)
    
    loaded = load_state_file(state_file)
    assert loaded["project_id"] == "TEST-001"
    assert loaded["state"] == "initializing"

def test_load_state_file_missing(temp_state_dir):
    """Test loading a non-existent state file returns default structure."""
    state_file = temp_state_dir / "nonexistent.yaml"
    loaded = load_state_file(state_file)
    
    assert "project_id" in loaded
    assert "state" in loaded
    assert "artifacts" in loaded
    assert "created_at" in loaded

def test_compute_artifact_checksums(sample_artifact):
    """Test computing checksums for artifacts."""
    checksums = compute_artifact_checksums([sample_artifact])
    
    assert len(checksums) == 1
    assert str(sample_artifact) in checksums
    expected_checksum = calculate_sha256(sample_artifact)
    assert checksums[str(sample_artifact)] == expected_checksum

def test_compute_artifact_checksums_missing_file():
    """Test handling of missing files in checksum computation."""
    missing_path = Path("/nonexistent/path/file.txt")
    checksums = compute_artifact_checksums([missing_path])
    
    assert len(checksums) == 0

@patch('utils.versioning.get_project_id')
@patch('utils.versioning.Paths')
def test_get_state_file_path(mock_paths, mock_get_project_id, temp_state_dir):
    """Test constructing the state file path."""
    mock_get_project_id.return_value = "PROJ-TEST-123"
    mock_paths.STATE_DIR = temp_state_dir
    
    result = get_state_file_path()
    
    assert "projects" in str(result)
    assert "PROJ-TEST-123.yaml" in str(result)

@patch('utils.versioning.get_project_id')
@patch('utils.versioning.Paths')
def test_update_state_file(mock_paths, mock_get_project_id, temp_state_dir, sample_artifact):
    """Test updating state file with new artifacts."""
    mock_get_project_id.return_value = "PROJ-TEST-456"
    mock_paths.STATE_DIR = temp_state_dir
    
    state_file = temp_state_dir / "projects" / "PROJ-TEST-456.yaml"
    
    # Create initial state
    initial_state = {
        "project_id": "PROJ-TEST-456",
        "state": "initializing",
        "artifacts": {}
    }
    with open(state_file, 'w') as f:
        yaml.dump(initial_state, f)
    
    # Update with new artifact
    updated_state = update_state_file(
        state_path=state_file,
        new_artifacts=[sample_artifact],
        status="data_generated"
    )
    
    assert updated_state["state"] == "data_generated"
    assert len(updated_state["artifacts"]) == 1
    assert str(sample_artifact) in updated_state["artifacts"]
    assert "checksum" in updated_state["artifacts"][str(sample_artifact)]
    assert "updated_at" in updated_state["artifacts"][str(sample_artifact)]

@patch('utils.versioning.get_state_file_path')
@patch('utils.versioning.update_state_file')
def test_record_data_generation_state(mock_update, mock_get_path, temp_state_dir, sample_artifact):
    """Test the convenience function for recording data generation state."""
    mock_get_path.return_value = temp_state_dir / "test.yaml"
    mock_update.return_value = {"status": "success"}
    
    result = record_data_generation_state(
        generated_files=[sample_artifact],
        status="data_generated"
    )
    
    mock_update.assert_called_once()
    assert result == {"status": "success"}

@patch('utils.versioning.get_project_id')
@patch('utils.versioning.Paths')
def test_update_state_file_with_metadata(mock_paths, mock_get_project_id, temp_state_dir):
    """Test updating state file with metadata updates."""
    mock_get_project_id.return_value = "PROJ-META-789"
    mock_paths.STATE_DIR = temp_state_dir
    
    state_file = temp_state_dir / "projects" / "PROJ-META-789.yaml"
    
    # Create initial state with metadata
    initial_state = {
        "project_id": "PROJ-META-789",
        "metadata": {"existing_key": "existing_value"}
    }
    with open(state_file, 'w') as f:
        yaml.dump(initial_state, f)
    
    # Update with metadata
    updated_state = update_state_file(
        state_path=state_file,
        metadata_updates={"new_key": "new_value", "existing_key": "updated_value"}
    )
    
    assert updated_state["metadata"]["new_key"] == "new_value"
    assert updated_state["metadata"]["existing_key"] == "updated_value"
