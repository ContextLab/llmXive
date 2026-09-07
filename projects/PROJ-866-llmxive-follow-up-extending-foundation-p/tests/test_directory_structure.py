import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
    "state",
    "state/projects",
    "contracts"
]

@pytest.fixture
def project_root():
    """Returns the current working directory as the project root."""
    return Path.cwd()

def test_required_directories_exist(project_root):
    """
    Verifies that all required project directories exist.
    
    This test ensures the directory structure created by T001a is present:
    - code/
    - data/
    - data/raw/
    - data/processed/
    - data/results/
    - tests/
    - state/
    - state/projects/
    - contracts/
    """
    missing_dirs = []
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        elif not full_path.is_dir():
            missing_dirs.append(f"{dir_path} (is not a directory)")
    
    assert len(missing_dirs) == 0, f"Missing required directories: {missing_dirs}"

def test_directory_hierarchy(project_root):
    """
    Verifies the nested hierarchy of data and state directories.
    """
    # Check data hierarchy
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    data_results = project_root / "data" / "results"
    
    assert data_raw.exists(), "data/raw directory missing"
    assert data_processed.exists(), "data/processed directory missing"
    assert data_results.exists(), "data/results directory missing"
    
    # Check state hierarchy
    state_projects = project_root / "state" / "projects"
    assert state_projects.exists(), "state/projects directory missing"