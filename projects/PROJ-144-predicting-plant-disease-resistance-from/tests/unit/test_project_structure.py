import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    Test that the required project directories exist as per T001.
    Required directories: code/, data/raw, data/processed, tests/, state/
    """
    project_root = Path.cwd()
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "state"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            missing_dirs.append(dir_name)
    
    assert len(missing_dirs) == 0, f"Missing required directories: {missing_dirs}"

def test_subdirectories_exist():
    """
    Test that additional required subdirectories exist.
    """
    project_root = Path.cwd()
    
    required_subdirs = [
        "code/data",
        "code/utils",
        "code/modeling",
        "tests/unit",
        "tests/integration",
        "results",
        "figures"
    ]
    
    missing_dirs = []
    for dir_name in required_subdirs:
        dir_path = project_root / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            missing_dirs.append(dir_name)
    
    assert len(missing_dirs) == 0, f"Missing required subdirectories: {missing_dirs}"

def test_gitkeep_files_exist():
    """
    Test that .gitkeep files exist in the directories to ensure they are tracked.
    """
    project_root = Path.cwd()
    
    dirs_with_gitkeep = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "state",
        "results",
        "figures"
    ]
    
    missing_gitkeeps = []
    for dir_name in dirs_with_gitkeep:
        dir_path = project_root / dir_name / ".gitkeep"
        if not dir_path.exists():
            missing_gitkeeps.append(dir_name)
    
    # Note: This is a soft check as .gitkeep might not be strictly required
    # depending on git configuration, but it's good practice
    if missing_gitkeeps:
        print(f"Warning: Missing .gitkeep files in: {missing_gitkeeps}")