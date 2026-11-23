import os
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

from state_manager import (
    initialize_state_file,
    load_state,
    save_state,
    calculate_file_hash,
    register_artifact,
    verify_artifact,
    list_registered_artifacts
)

@pytest.fixture
def temp_state_file():
    """Create a temporary state.yaml file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_data_file():
    """Create a temporary data file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("test content for hashing")
        yield Path(f.name)
    os.unlink(f.name)

def test_initialize_state_file(temp_state_file):
    """Test that initialize_state_file creates a valid skeleton."""
    initialize_state_file(temp_state_file)
    
    assert temp_state_file.exists()
    state = load_state(temp_state_file)
    
    assert "project_id" in state
    assert "created_at" in state
    assert "last_updated" in state
    assert "artifacts" in state
    assert isinstance(state["artifacts"], dict)

def test_load_state_creates_if_missing(temp_state_file):
    """Test that load_state initializes the file if it doesn't exist."""
    # Ensure file doesn't exist
    if temp_state_file.exists():
        os.unlink(temp_state_file)
        
    state = load_state(temp_state_file)
    
    assert temp_state_file.exists()
    assert "artifacts" in state

def test_calculate_file_hash(temp_data_file):
    """Test that calculate_file_hash returns a valid SHA-256 hash."""
    file_hash = calculate_file_hash(temp_data_file)
    
    assert isinstance(file_hash, str)
    assert len(file_hash) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in file_hash)

def test_register_artifact(temp_state_file, temp_data_file):
    """Test that register_artifact correctly adds an artifact to state."""
    artifact_name = "test_artifact"
    description = "A test artifact"
    
    register_artifact(temp_state_file, artifact_name, temp_data_file, description)
    
    state = load_state(temp_state_file)
    
    assert artifact_name in state["artifacts"]
    artifact = state["artifacts"][artifact_name]
    
    assert artifact["path"] == str(temp_data_file)
    assert "hash" in artifact
    assert "registered_at" in artifact
    assert artifact["description"] == description

def test_verify_artifact_valid(temp_state_file, temp_data_file):
    """Test verify_artifact returns True for a valid, unchanged artifact."""
    register_artifact(temp_state_file, "valid_artifact", temp_data_file)
    
    assert verify_artifact(temp_state_file, "valid_artifact") is True

def test_verify_artifact_modified(temp_state_file, temp_data_file):
    """Test verify_artifact returns False when file is modified."""
    register_artifact(temp_state_file, "modified_artifact", temp_data_file)
    
    # Modify the file
    with open(temp_data_file, "w") as f:
        f.write("modified content")
    
    assert verify_artifact(temp_state_file, "modified_artifact") is False

def test_verify_artifact_missing(temp_state_file):
    """Test verify_artifact returns False when file doesn't exist."""
    # Register a path that doesn't exist
    state = load_state(temp_state_file)
    state["artifacts"] = {
        "missing_artifact": {
            "path": "/non/existent/path.txt",
            "hash": "dummy_hash",
            "registered_at": datetime.utcnow().isoformat()
        }
    }
    save_state(temp_state_file, state)
    
    assert verify_artifact(temp_state_file, "missing_artifact") is False

def test_list_registered_artifacts(temp_state_file, temp_data_file):
    """Test list_registered_artifacts returns all registered artifacts."""
    register_artifact(temp_state_file, "art1", temp_data_file)
    register_artifact(temp_state_file, "art2", temp_data_file)
    
    artifacts = list_registered_artifacts(temp_state_file)
    
    assert len(artifacts) == 2
    assert "art1" in artifacts
    assert "art2" in artifacts
