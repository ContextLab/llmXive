"""
Unit tests for state_management module (T007).
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import pytest

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from state_management import (
    init_state_file, 
    update_state, 
    get_state, 
    add_task_status,
    log_artifact
)
from config import get_path as config_get_path


class MockConfig:
    """Mock config to override get_path for testing"""
    def __init__(self, temp_dir):
        self.temp_dir = Path(temp_dir)
    
    def get_path(self, key):
        if key == "state":
            return self.temp_dir / "state"
        return self.temp_dir / key


@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files during tests"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


def test_init_state_file_creates_structure(temp_state_dir):
    """Test that init_state_file creates the directory and state.yaml"""
    # Temporarily override get_path
    import state_management
    original_get_path = state_management.get_path
    state_management.get_path = lambda key: Path(temp_state_dir) / key

    try:
        project_id = "TEST-001"
        state_file = init_state_file(project_id)
        
        assert state_file.exists()
        assert state_file.name == "state.yaml"
        
        # Check content
        with open(state_file, 'r') as f:
            content = yaml.safe_load(f)
        
        assert content["project_id"] == project_id
        assert "created_at" in content
        assert "last_modified" in content
        assert "version" in content
        assert "principle_v" in content
        assert "tasks" in content
    finally:
        state_management.get_path = original_get_path


def test_init_state_file_updates_timestamp(temp_state_dir):
    """Test that calling init_state_file again updates the timestamp"""
    import state_management
    original_get_path = state_management.get_path
    state_management.get_path = lambda key: Path(temp_state_dir) / key

    try:
        project_id = "TEST-002"
        state_file = init_state_file(project_id)
        
        with open(state_file, 'r') as f:
            first_content = yaml.safe_load(f)
        
        import time
        time.sleep(0.1)  # Small delay to ensure timestamp change
        
        init_state_file(project_id)
        
        with open(state_file, 'r') as f:
            second_content = yaml.safe_load(f)
        
        assert first_content["last_modified"] != second_content["last_modified"]
    finally:
        state_management.get_path = original_get_path


def test_update_state(temp_state_dir):
    """Test updating state with new values"""
    import state_management
    original_get_path = state_management.get_path
    state_management.get_path = lambda key: Path(temp_state_dir) / key

    try:
        project_id = "TEST-003"
        init_state_file(project_id)
        
        updates = {
            "version": "0.2.0",
            "custom_field": "test_value"
        }
        
        result = update_state(project_id, updates)
        
        assert result["version"] == "0.2.0"
        assert result["custom_field"] == "test_value"
    finally:
        state_management.get_path = original_get_path


def test_add_task_status(temp_state_dir):
    """Test adding task status to state"""
    import state_management
    original_get_path = state_management.get_path
    state_management.get_path = lambda key: Path(temp_state_dir) / key

    try:
        project_id = "TEST-004"
        init_state_file(project_id)
        
        add_task_status(project_id, "T001", "completed")
        
        state = get_state(project_id)
        assert "T001" in state["tasks"]["completed"]
        
        add_task_status(project_id, "T001", "in_progress")
        
        state = get_state(project_id)
        assert "T001" not in state["tasks"]["completed"]
        assert "T001" in state["tasks"]["in_progress"]
    finally:
        state_management.get_path = original_get_path


def test_log_artifact(temp_state_dir):
    """Test logging an artifact to state"""
    import state_management
    import hashlib
    original_get_path = state_management.get_path
    state_management.get_path = lambda key: Path(temp_state_dir) / key

    try:
        project_id = "TEST-005"
        init_state_file(project_id)
        
        # Create a dummy file
        dummy_file = Path(temp_state_dir) / "dummy.txt"
        dummy_file.write_text("test content")
        
        log_artifact(project_id, str(dummy_file))
        
        state = get_state(project_id)
        artifacts = state["principle_v"]["artifacts"]
        
        assert len(artifacts) == 1
        assert artifacts[0]["path"] == str(dummy_file)
        assert "checksum" in artifacts[0]
        
        # Verify checksum
        expected_checksum = hashlib.sha256(b"test content").hexdigest()
        assert artifacts[0]["checksum"] == expected_checksum
    finally:
        state_management.get_path = original_get_path
