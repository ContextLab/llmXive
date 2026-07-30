"""
Unit tests to verify the project directory structure is correctly created.
"""
import os
import pytest
import sys
from pathlib import Path

def test_project_directories_exist():
    """
    Test that all required directories from T001a exist.
    """
    # Get project root (parent of tests directory)
    test_file = Path(__file__).resolve()
    project_root = test_file.parent.parent.parent
    
    required_dirs = [
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "scripts",
        "data/results",
        "data/logs",
        "data/configs",
        "state",
        # T001b directories
        "data/raw",
        "data/processed",
        "data/interim",
        # T001c directories
        "tests/unit/models",
        "tests/unit/data",
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing_dirs.append(dir_path)
    
    assert len(missing_dirs) == 0, f"Missing directories: {missing_dirs}"

def test_project_root_is_valid():
    """
    Test that the project root contains essential files/directories.
    """
    # Get project root
    test_file = Path(__file__).resolve()
    project_root = test_file.parent.parent.parent
    
    # Check for src directory
    assert (project_root / "src").exists(), "src directory missing"
    
    # Check for tests directory
    assert (project_root / "tests").exists(), "tests directory missing"
    
    # Check for scripts directory
    assert (project_root / "scripts").exists(), "scripts directory missing"
    
    # Check for data directory
    assert (project_root / "data").exists(), "data directory missing"
    
    # Check for state directory
    assert (project_root / "state").exists(), "state directory missing"
