import os
import json
import yaml
from pathlib import Path
import tempfile
import pytest
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_state import ensure_state_directories, create_initial_project_state, update_project_state

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        yield project_root

def test_ensure_state_directories_creates_structure(temp_project_root):
    """Test that ensure_state_directories creates the required directories."""
    ensure_state_directories(temp_project_root)
    
    state_dir = temp_project_root / "state"
    projects_dir = state_dir / "projects"
    
    assert state_dir.exists(), "state/ directory should exist"
    assert state_dir.is_dir(), "state/ should be a directory"
    assert projects_dir.exists(), "state/projects/ directory should exist"
    assert projects_dir.is_dir(), "state/projects/ should be a directory"

def test_create_initial_project_state_creates_file(temp_project_root):
    """Test that create_initial_project_state creates the YAML file."""
    project_id = "TEST-001"
    state_file = create_initial_project_state(temp_project_root, project_id)
    
    expected_path = temp_project_root / "state" / "projects" / f"{project_id}.yaml"
    
    assert state_file == expected_path, f"State file path mismatch: {state_file} != {expected_path}"
    assert state_file.exists(), "State file should exist"
    assert state_file.suffix == ".yaml", "State file should have .yaml extension"

def test_create_initial_project_state_structure(temp_project_root):
    """Test that the created state file has the correct structure."""
    project_id = "TEST-001"
    state_file = create_initial_project_state(temp_project_root, project_id)
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert state["project_id"] == project_id
    assert state["status"] == "initialized"
    assert "created_at" in state
    assert "last_updated" in state
    assert "phases" in state
    assert "metadata" in state
    
    # Check phase structure
    phases = state["phases"]
    assert "phase_1_setup" in phases
    assert "phase_2_foundational" in phases
    assert "phase_3_us1" in phases
    assert "phase_4_us2" in phases
    assert "phase_5_us3" in phases
    
    for phase_name, phase_data in phases.items():
        assert "status" in phase_data
        assert "tasks_completed" in phase_data
        assert phase_data["status"] == "pending"
        assert phase_data["tasks_completed"] == []

def test_update_project_state(temp_project_root):
    """Test that update_project_state correctly updates the file."""
    project_id = "TEST-001"
    state_file = create_initial_project_state(temp_project_root, project_id)
    
    updates = {
        "status": "in_progress",
        "phases": {
            "phase_1_setup": {
                "status": "completed",
                "tasks_completed": ["T001a", "T001b"]
            }
        }
    }
    
    updated_file = update_project_state(temp_project_root, project_id, updates)
    
    assert updated_file == state_file
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert state["status"] == "in_progress"
    assert state["phases"]["phase_1_setup"]["status"] == "completed"
    assert state["phases"]["phase_1_setup"]["tasks_completed"] == ["T001a", "T001b"]
    assert "last_updated" in state

def test_update_project_state_nonexistent_file(temp_project_root):
    """Test that update_project_state raises error for missing file."""
    project_id = "TEST-MISSING"
    
    with pytest.raises(FileNotFoundError):
        update_project_state(temp_project_root, project_id, {"status": "test"})
