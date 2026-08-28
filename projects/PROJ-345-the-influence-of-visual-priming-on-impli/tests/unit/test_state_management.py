"""
Unit tests for state management functionality.
Tests the initialization and manipulation of state.yaml for Principle V.
"""
import os
import yaml
import pytest
from pathlib import Path
import tempfile
import shutil

# Mock config to use temp directories for testing
import sys
from unittest.mock import patch

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure for testing."""
    temp_base = tempfile.mkdtemp()
    temp_state = Path(temp_base) / "state"
    temp_project = temp_state / "PROJ-345"
    temp_project.mkdir(parents=True)
    
    # Mock the config.get_path function
    def mock_get_path(key):
        if key == "state":
            return temp_state
        return Path("/mock/path")
    
    with patch('state_management.get_path', side_effect=mock_get_path):
        yield temp_project
    
    shutil.rmtree(temp_base)

@pytest.fixture
def mock_config():
    """Patch config.get_path to return predictable paths."""
    def mock_get_path(key):
        return Path(f"/mock/{key}")
    
    with patch('state_management.get_path', side_effect=mock_get_path):
        yield

def test_init_state_file_creates_structure(temp_project_dir):
    """Test that init_state_file creates the required directory and file."""
    from state_management import init_state_file, get_project_state_dir
    
    # Reset the directory to be empty
    for f in temp_project_dir.iterdir():
        f.unlink()
    
    state_file = init_state_file("PROJ-345")
    
    assert state_file.exists()
    assert state_file.name == "state.yaml"
    
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data["project_id"] == "PROJ-345"
    assert "created_at" in data
    assert "updated_at" in data
    assert data["principle_v_enabled"] is True
    assert "artifacts" in data
    assert "execution_log" in data

def test_init_state_file_idempotent(temp_project_dir):
    """Test that calling init_state_file twice doesn't overwrite existing data."""
    from state_management import init_state_file
    
    # First init
    state_file = init_state_file("PROJ-345")
    with open(state_file, 'r') as f:
        first_data = yaml.safe_load(f)
    
    # Modify the file
    first_data["custom_field"] = "test_value"
    with open(state_file, 'w') as f:
        yaml.dump(first_data, f)
    
    # Second init
    state_file_2 = init_state_file("PROJ-345")
    with open(state_file_2, 'r') as f:
        second_data = yaml.safe_load(f)
    
    # Should preserve the custom field
    assert second_data["custom_field"] == "test_value"

def test_add_artifact_record(temp_project_dir):
    """Test adding an artifact record to state.yaml."""
    from state_management import init_state_file, add_artifact_record
    
    init_state_file("PROJ-345")
    
    add_artifact_record(
        "PROJ-345",
        "data/processed/linked_trials.csv",
        "csv",
        "abc123checksum"
    )
    
    state_file = get_project_state_dir("PROJ-345") / "state.yaml"
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert len(data["artifacts"]) == 1
    assert data["artifacts"][0]["path"] == "data/processed/linked_trials.csv"
    assert data["artifacts"][0]["type"] == "csv"
    assert data["artifacts"][0]["checksum"] == "abc123checksum"

def test_log_execution(temp_project_dir):
    """Test logging an execution event."""
    from state_management import init_state_file, log_execution
    
    init_state_file("PROJ-345")
    
    log_execution("PROJ-345", "T007", "success", duration_seconds=1.5)
    
    state_file = get_project_state_dir("PROJ-345") / "state.yaml"
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert len(data["execution_log"]) == 1
    assert data["execution_log"][0]["task_id"] == "T007"
    assert data["execution_log"][0]["status"] == "success"
    assert data["execution_log"][0]["duration_seconds"] == 1.5

def test_log_execution_failure(temp_project_dir):
    """Test logging a failed execution."""
    from state_management import init_state_file, log_execution
    
    init_state_file("PROJ-345")
    
    log_execution("PROJ-345", "T007", "failed", error="Simulated error")
    
    state_file = get_project_state_dir("PROJ-345") / "state.yaml"
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert len(data["execution_log"]) == 1
    assert data["execution_log"][0]["status"] == "failed"
    assert data["execution_log"][0]["error"] == "Simulated error"

def test_save_state_file_updates_timestamp(temp_project_dir):
    """Test that save_state_file updates the timestamp."""
    from state_management import init_state_file, save_state_file
    import time
    
    init_state_file("PROJ-345")
    
    state_file = get_project_state_dir("PROJ-345") / "state.yaml"
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    first_updated = data["updated_at"]
    
    time.sleep(0.01)  # Small delay to ensure timestamp changes
    
    save_state_file("PROJ-345", {"test_key": "test_value"})
    
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data["updated_at"] != first_updated
    assert data["test_key"] == "test_value"