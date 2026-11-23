"""Unit tests for config utility functions (ensure_directories, load_state, save_state)."""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

from config import ensure_directories, load_state, save_state, STATE_DIR

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure."""
    root = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(root)
    yield root
    os.chdir(original_cwd)
    shutil.rmtree(root)

def test_ensure_directories_creates_structure(temp_project_root):
    """Test that ensure_directories creates the required paths."""
    # The function should create state and data dirs
    ensure_directories()
    
    # Check state dir exists
    assert os.path.exists(STATE_DIR)
    
    # Check subdirectories from config.py (RAW_DATA_DIR, etc.)
    # We assume config.py defines these and ensure_directories creates them
    # Since we can't import them directly without circular deps or specific imports,
    # we check the base directories that are known to be created.
    assert os.path.exists(os.path.join(os.getcwd(), "data"))
    assert os.path.exists(os.path.join(os.getcwd(), "state"))

def test_load_state_empty_file(temp_project_root):
    """Test loading state from an empty or non-existent file."""
    state_file = Path(STATE_DIR) / "PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # If file doesn't exist, it should return default structure
    state = load_state()
    assert isinstance(state, dict)
    assert "artifact_hashes" in state

def test_load_state_with_data(temp_project_root):
    """Test loading state from a file with existing data."""
    state_file = Path(STATE_DIR) / "PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_data = {
        "checkpoint": {"last_workflow_id": 10, "status": "running"},
        "artifact_hashes": {"file.txt": "abc123"}
    }
    state_file.write_text(json.dumps(test_data)) # YAML is compatible with JSON for simple dicts in this context or we assume yaml lib is used internally
    
    state = load_state()
    assert state["checkpoint"]["last_workflow_id"] == 10
    assert state["artifact_hashes"]["file.txt"] == "abc123"

def test_save_state_writes_file(temp_project_root):
    """Test that save_state writes data correctly."""
    test_data = {
        "checkpoint": {"last_workflow_id": 5, "status": "done"},
        "artifact_hashes": {"new.txt": "def456"}
    }
    
    save_state(test_data)
    
    state_file = Path(STATE_DIR) / "PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml"
    assert state_file.exists()
    
    loaded = load_state()
    assert loaded["checkpoint"]["last_workflow_id"] == 5
    assert loaded["artifact_hashes"]["new.txt"] == "def456"
