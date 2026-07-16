"""
Unit tests for T001: Project structure creation.

Verifies that the required directories exist after running setup_data_structure.py
"""
import os
from pathlib import Path
import pytest

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/derived",
    "data/processed",
    "tests",
    "state",
]

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(".")

def test_required_directories_exist(project_root):
    """Test that all required directories exist in the project structure."""
    missing_dirs = []
    for dir_name in REQUIRED_DIRS:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
        elif not dir_path.is_dir():
            missing_dirs.append(f"{dir_name} (not a directory)")
    
    assert not missing_dirs, f"Missing required directories: {', '.join(missing_dirs)}"

def test_subdirectories_exist(project_root):
    """Test that key subdirectories exist."""
    required_subdirs = [
        "data/raw/eye_tracking",
        "data/derived/synthetic",
        "data/processed/cleaned",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "figures",
    ]
    
    missing_subdirs = []
    for subdir in required_subdirs:
        subdir_path = project_root / subdir
        if not subdir_path.exists():
            missing_subdirs.append(subdir)
    
    assert not missing_subdirs, f"Missing required subdirectories: {', '.join(missing_subdirs)}"

def test_gitkeep_files_exist(project_root):
    """Test that .gitkeep files exist in directories to ensure git tracking."""
    for dir_name in REQUIRED_DIRS:
        gitkeep_path = project_root / dir_name / ".gitkeep"
        assert gitkeep_path.exists(), f"Missing .gitkeep in {dir_name}"
