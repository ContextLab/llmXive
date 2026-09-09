import pytest
import yaml
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

# We need to mock the config.get_path to point to a temp directory during tests
# to avoid writing to the actual project state directory during unit tests.

@pytest.fixture
def temp_state_root(tmp_path):
    """Create a temporary directory to act as the state root for testing."""
    return tmp_path

@pytest.fixture
def mock_config(temp_state_root):
    """Mock the config.get_path function to return our temp directory."""
    def mock_get_path(subpath):
        return temp_state_root / subpath
    
    with patch('state_management.get_path', mock_get_path):
        yield

def test_init_state_file_creates_structure(mock_config, temp_state_root):
    """Test that init_state_file creates the directory and state.yaml."""
    from state_management import init_state_file, get_project_state_dir
    
    project_id = "TEST-001"
    state_path = init_state_file(project_id)
    
    # Check directory exists
    project_dir = get_project_state_dir(project_id)
    assert project_dir.exists()
    
    # Check file exists
    assert state_path.exists()
    assert state_path.name == "state.yaml"
    
    # Check content
    with open(state_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data["project_id"] == project_id
    assert "created_at" in data
    assert "updated_at" in data
    assert "version" in data
    assert data["principles"]["V"]["name"] == "Versioning"
    assert "artifacts" in data
    assert "execution_history" in data

def test_init_state_file_idempotent(mock_config, temp_state_root):
    """Test that calling init_state_file twice doesn't break the file."""
    from state_management import init_state_file
    
    project_id = "TEST-002"
    path1 = init_state_file(project_id)
    path2 = init_state_file(project_id)
    
    assert path1 == path2
    assert path1.exists()
    
    with open(path1, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data["project_id"] == project_id

def test_add_artifact_record(mock_config, temp_state_root):
    """Test adding an artifact record to state."""
    from state_management import init_state_file, add_artifact_record
    
    project_id = "TEST-003"
    init_state_file(project_id)
    
    add_artifact_record(
        project_id, 
        "data/processed/test.csv", 
        checksum="abc123", 
        description="Test artifact"
    )
    
    state_path = temp_state_root / "projects" / project_id / "state.yaml"
    with open(state_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert len(data["artifacts"]) == 1
    assert data["artifacts"][0]["path"] == "data/processed/test.csv"
    assert data["artifacts"][0]["checksum"] == "abc123"
    assert data["artifacts"][0]["description"] == "Test artifact"

def test_log_execution(mock_config, temp_state_root):
    """Test logging an execution event."""
    from state_management import init_state_file, log_execution
    
    project_id = "TEST-004"
    init_state_file(project_id)
    
    log_execution(project_id, "T007", "completed", {"duration": 1.5})
    
    state_path = temp_state_root / "projects" / project_id / "state.yaml"
    with open(state_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert len(data["execution_history"]) == 1
    assert data["execution_history"][0]["task_id"] == "T007"
    assert data["execution_history"][0]["status"] == "completed"
    assert data["execution_history"][0]["details"]["duration"] == 1.5