import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Mock config for testing
@pytest.fixture
def mock_config(tmp_path):
    # Create a temporary directory structure
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    
    # Mock the Paths and get_project_id
    with patch('utils.versioning.Paths') as mock_paths, \
         patch('utils.versioning.get_project_id', return_value="TEST-PROJECT-001"):
        
        mock_paths.state = tmp_path / "state"
        mock_paths.root = tmp_path
        
        yield tmp_path


def test_get_state_file_path(mock_config):
    from utils.versioning import get_state_file_path
    
    path = get_state_file_path()
    assert path.name == "TEST-PROJECT-001.yaml"
    assert "projects" in str(path)


def test_load_state_file_new(mock_config):
    from utils.versioning import load_state_file, get_state_file_path
    
    path = get_state_file_path()
    state = load_state_file(path)
    
    assert "project_id" in state
    assert state["project_id"] == "TEST-PROJECT-001"
    assert "artifacts" in state
    assert "checksums" in state


def test_update_state_file(mock_config):
    from utils.versioning import load_state_file, update_state_file, get_state_file_path
    
    path = get_state_file_path()
    state = load_state_file(path)
    state["test_key"] = "test_value"
    
    update_state_file(state, path)
    
    # Reload and verify
    with open(path, 'r') as f:
        reloaded = yaml.safe_load(f)
    
    assert reloaded["test_key"] == "test_value"
    assert "updated_at" in reloaded


def test_compute_artifact_checksums(mock_config):
    from utils.versioning import compute_artifact_checksums
    
    # Create a dummy file
    dummy_file = mock_config / "dummy.txt"
    dummy_file.write_text("hello world")
    
    checksums = compute_artifact_checksums([dummy_file])
    
    assert len(checksums) == 1
    # Verify it's a valid hex string (SHA256 is 64 chars)
    checksum = list(checksums.values())[0]
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)


def test_record_data_generation_state(mock_config):
    from utils.versioning import record_data_generation_state, load_state_file, get_state_file_path
    
    # Create a dummy artifact
    artifact = mock_config / "data" / "processed" / "test.parquet"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("fake parquet data")
    
    record_data_generation_state([artifact], metadata={"test": "meta"})
    
    state_path = get_state_file_path()
    state = load_state_file(state_path)
    
    assert "TEST-PROJECT-001" in str(state_path)
    assert "metadata" in state
    assert state["metadata"]["test"] == "meta"
    assert str(artifact.relative_to(mock_config)) in state["checksums"]
    assert str(artifact.relative_to(mock_config)) in state["artifacts"]