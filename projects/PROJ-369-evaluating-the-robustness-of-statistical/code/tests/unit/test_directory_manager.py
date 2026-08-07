import os
from pathlib import Path
import pytest
import yaml
from src.utils.directory_manager import (
    setup_project_directories,
    initialize_checksums
)
from src.utils.config import get_path
from src.utils.checksums import load_state

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for testing"""
    # We can't easily mock get_path to use tmp_path without more complex mocking,
    # so we'll test the logic by checking that directories exist after setup
    return tmp_path

def test_setup_directories_creates_all_required():
    """Test that setup_project_directories creates all required directories"""
    # Run the setup
    created_dirs = setup_project_directories()
    
    # Check that all required directories were created or already existed
    required_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "state",
        "state/projects"
    ]
    
    for dir_name in required_dirs:
        dir_path = get_path(dir_name)
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

def test_initialize_checksums_creates_state_file():
    """Test that initialize_checksums creates the state file"""
    # Run initialization
    initialize_checksums()
    
    # Check that state file exists
    project_id = "PROJ-369-evaluating-the-robustness-of-statistical"
    state_file = get_path("state/projects") / f"{project_id}.yaml"
    
    assert state_file.exists(), "State file was not created"
    
    # Verify the state file has the correct structure
    state = load_state(project_id)
    assert state is not None, "Could not load state file"
    assert "project_id" in state, "State file missing project_id"
    assert "checksums" in state, "State file missing checksums"
    assert state["project_id"] == project_id, "Project ID mismatch in state file"
    
    # Verify checksums for required directories are present
    required_dirs = ["data/raw", "data/processed", "results"]
    for dir_name in required_dirs:
        assert dir_name in state["checksums"], f"Missing checksums for {dir_name}"
