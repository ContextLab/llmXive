"""
Unit tests for the state_manager module.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

from src.utils.state_manager import (
    compute_file_hash,
    get_state_file_path,
    load_state,
    update_state_artifact,
    verify_artifact_integrity
)
from src.utils.config import get_project_root, set_seed

# Fix seed for deterministic behavior if needed
set_seed(42)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_file_hash(temp_dir):
    """Test SHA-256 hash computation."""
    test_file = temp_dir / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    computed_hash = compute_file_hash(test_file)
    expected_hash = hashlib.sha256(content).hexdigest()
    
    assert computed_hash == expected_hash
    assert len(computed_hash) == 64  # SHA-256 hex length

def test_get_state_file_path(temp_dir):
    """Test state file path generation."""
    # This test assumes the config is set up correctly in the environment.
    # We just verify the function returns a Path object.
    state_path = get_state_file_path()
    assert isinstance(state_path, Path)
    assert state_path.suffix == ".yaml"

def test_load_state_empty(temp_dir, monkeypatch):
    """Test loading state when file does not exist."""
    # Mock the get_state_root to return our temp dir
    def mock_get_state_root():
        return temp_dir
    
    monkeypatch.setattr("src.utils.state_manager.get_state_root", mock_get_state_root)
    
    state = load_state()
    
    assert "project_id" in state
    assert "created_at" in state
    assert "artifacts" in state
    assert isinstance(state["artifacts"], dict)

def test_load_state_existing(temp_dir, monkeypatch):
    """Test loading state when file exists."""
    def mock_get_state_root():
        return temp_dir
    
    monkeypatch.setattr("src.utils.state_manager.get_state_root", mock_get_state_root)
    
    # Create a dummy state file
    state_file = temp_dir / "PROJ-206-statistical-analysis-of-publicly-availab.yaml"
    initial_state = {
        "project_id": "PROJ-206-test",
        "created_at": "2023-01-01T00:00:00",
        "artifacts": {
            "test_artifact": {
                "path": "data/test.csv",
                "hash": "abc123",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    }
    
    with open(state_file, "w") as f:
        yaml.dump(initial_state, f)
        
    state = load_state()
    
    assert state["project_id"] == "PROJ-206-test"
    assert "test_artifact" in state["artifacts"]
    assert state["artifacts"]["test_artifact"]["hash"] == "abc123"

def test_update_state_artifact(temp_dir, monkeypatch):
    """Test updating state with a new artifact."""
    def mock_get_state_root():
        return temp_dir
    
    def mock_get_project_root():
        return temp_dir.parent / "mock_project" # Just needs to exist for relative resolution
    
    # Ensure the mock project root exists
    mock_proj = temp_dir.parent / "mock_project"
    mock_proj.mkdir(exist_ok=True)
    
    monkeypatch.setattr("src.utils.state_manager.get_state_root", mock_get_state_root)
    monkeypatch.setattr("src.utils.state_manager.get_project_root", mock_get_project_root)
    
    # Create a dummy artifact file
    artifact_path = temp_dir / "data"
    artifact_path.mkdir(exist_ok=True)
    test_file = artifact_path / "test.csv"
    test_file.write_text("col1,col2\n1,2\n")
    
    # Update state
    update_state_artifact("test_artifact", str(test_file), "Test description")
    
    # Verify state file was updated
    state_file = temp_dir / "PROJ-206-statistical-analysis-of-publicly-availab.yaml"
    assert state_file.exists()
    
    with open(state_file, "r") as f:
        state = yaml.safe_load(f)
        
    assert "artifacts" in state
    assert "test_artifact" in state["artifacts"]
    assert state["artifacts"]["test_artifact"]["description"] == "Test description"
    assert state["artifacts"]["test_artifact"]["path"] == "data/test.csv"
    assert len(state["artifacts"]["test_artifact"]["hash"]) == 64

def test_verify_artifact_integrity_success(temp_dir, monkeypatch):
    """Test successful integrity verification."""
    def mock_get_state_root():
        return temp_dir
    
    def mock_get_project_root():
        return temp_dir.parent / "mock_project"
    
    mock_proj = temp_dir.parent / "mock_project"
    mock_proj.mkdir(exist_ok=True)
    
    monkeypatch.setattr("src.utils.state_manager.get_state_root", mock_get_state_root)
    monkeypatch.setattr("src.utils.state_manager.get_project_root", mock_get_project_root)
    
    # Create artifact and update state
    artifact_path = temp_dir / "data"
    artifact_path.mkdir(exist_ok=True)
    test_file = artifact_path / "test.csv"
    test_file.write_text("data")
    
    update_state_artifact("test_artifact", str(test_file))
    
    # Verify
    assert verify_artifact_integrity("test_artifact") is True

def test_verify_artifact_integrity_failure(temp_dir, monkeypatch):
    """Test integrity verification failure when file is modified."""
    def mock_get_state_root():
        return temp_dir
    
    def mock_get_project_root():
        return temp_dir.parent / "mock_project"
    
    mock_proj = temp_dir.parent / "mock_project"
    mock_proj.mkdir(exist_ok=True)
    
    monkeypatch.setattr("src.utils.state_manager.get_state_root", mock_get_state_root)
    monkeypatch.setattr("src.utils.state_manager.get_project_root", mock_get_project_root)
    
    # Create artifact and update state
    artifact_path = temp_dir / "data"
    artifact_path.mkdir(exist_ok=True)
    test_file = artifact_path / "test.csv"
    test_file.write_text("original")
    
    update_state_artifact("test_artifact", str(test_file))
    
    # Modify file
    test_file.write_text("modified")
    
    # Verify should fail
    assert verify_artifact_integrity("test_artifact") is False