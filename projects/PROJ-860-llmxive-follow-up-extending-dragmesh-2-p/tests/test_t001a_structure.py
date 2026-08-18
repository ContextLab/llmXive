import os
import pytest
from pathlib import Path

def test_project_directory_structure_exists():
    """
    Verify that the T001a task successfully created the required directory structure.
    This test checks for the existence of:
    - code
    - tests
    - data/raw
    - data/generated
    - state/projects
    - data/results
    """
    # Determine the project root (parent of the tests directory)
    # Assuming this test file is at tests/test_t001a_structure.py
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/generated",
        "state/projects",
        "data/results"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.is_dir():
            missing_dirs.append(dir_name)
    
    assert not missing_dirs, f"Required directories are missing: {missing_dirs}"

def test_data_raw_is_empty_or_exists():
    """
    Verify that data/raw exists (it should be empty initially or contain fetched data).
    """
    project_root = Path(__file__).parent.parent
    data_raw = project_root / "data" / "raw"
    assert data_raw.exists()
    assert data_raw.is_dir()

def test_state_projects_exists():
    """
    Verify that state/projects exists for storing state YAMLs.
    """
    project_root = Path(__file__).parent.parent
    state_projects = project_root / "state" / "projects"
    assert state_projects.exists()
    assert state_projects.is_dir()