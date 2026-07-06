import os
import json
import yaml
from pathlib import Path
import tempfile
import pytest

from setup_state import (
    ensure_state_directories,
    create_initial_project_state,
    update_project_state
)

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_ensure_state_directories_creates_structure(temp_project_root):
    """Test that ensure_state_directories creates the required directory structure."""
    ensure_state_directories(temp_project_root)
    
    state_dir = temp_project_root / "state"
    projects_dir = state_dir / "projects"
    
    assert state_dir.exists(), "state directory should exist"
    assert state_dir.is_dir(), "state should be a directory"
    assert projects_dir.exists(), "state/projects directory should exist"
    assert projects_dir.is_dir(), "state/projects should be a directory"

def test_create_initial_project_state_creates_file(temp_project_root):
    """Test that create_initial_project_state creates the YAML file."""
    project_id = "PROJ-TEST-001"
    state_file = create_initial_project_state(temp_project_root, project_id)
    
    expected_path = temp_project_root / "state" / "projects" / f"{project_id}.yaml"
    assert state_file.exists(), "State file should be created"
    assert state_file == expected_path, "State file should be in the correct location"

def test_create_initial_project_state_structure(temp_project_root):
    """Test that the created state file has the correct initial structure."""
    project_id = "PROJ-TEST-002"
    state_file = create_initial_project_state(temp_project_root, project_id)
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert state["project_id"] == project_id
    assert state["status"] == "initialized"
    assert "created_at" in state
    assert "updated_at" in state
    assert state["phase"] == "Phase 2: Foundational"
    assert isinstance(state["completed_tasks"], list)
    assert isinstance(state["metrics"], dict)
    assert isinstance(state["data_files"], dict)
    assert "raw" in state["data_files"]
    assert "processed" in state["data_files"]

def test_update_project_state(temp_project_root):
    """Test that update_project_state correctly updates the YAML file."""
    project_id = "PROJ-TEST-003"
    create_initial_project_state(temp_project_root, project_id)
    
    updates = {
        "status": "in_progress",
        "current_task": "T010",
        "metrics": {"test_metric": 42}
    }
    
    update_project_state(temp_project_root, project_id, updates)
    
    state_file = temp_project_root / "state" / "projects" / f"{project_id}.yaml"
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert state["status"] == "in_progress"
    assert state["current_task"] == "T010"
    assert state["metrics"]["test_metric"] == 42

def test_update_project_state_nonexistent_file(temp_project_root):
    """Test that update_project_state raises FileNotFoundError for missing file."""
    project_id = "PROJ-NONEXISTENT"
    
    with pytest.raises(FileNotFoundError):
        update_project_state(temp_project_root, project_id, {"status": "test"})
