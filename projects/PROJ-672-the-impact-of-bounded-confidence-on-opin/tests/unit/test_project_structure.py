"""
Unit tests for project structure initialization.
Verifies that T001 created the required directories and state file.
"""
import os
from pathlib import Path
import yaml
import pytest

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def test_directories_exist(project_root):
    """Test that all required directories were created."""
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/contract",
        "state/projects",
        "docs",
        "specs",
        "figures",
        "code/utils",
        "code/contracts",
        "code/explorers",
        "code/visualizations",
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_project_state_file_exists(project_root):
    """Test that the project state YAML file was initialized."""
    project_id = "PROJ-672-the-impact-of-bounded-confidence-on-opin"
    state_file = project_root / "state" / "projects" / f"{project_id}.yaml"
    
    assert state_file.exists(), f"Project state file {state_file} does not exist"
    
    # Verify it's valid YAML
    with open(state_file, 'r') as f:
        content = yaml.safe_load(f)
    
    assert content is not None
    assert "project_id" in content
    assert content["project_id"] == project_id
    assert "status" in content
    assert "phase" in content