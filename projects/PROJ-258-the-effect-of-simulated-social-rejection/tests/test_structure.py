"""
Tests for project structure creation (Task T001).
Verifies that the required directory hierarchy exists.
"""
import os
import pytest
from pathlib import Path

# Get the project root (two levels up from this test file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/interim",
    "data/processed",
    "data/figures",
    "tests",
    "reports",
    "docs",
    "specs",
    ".github/workflows"
]

def test_required_directories_exist():
    """
    Contract test: Asserts that all required directories for the project
    structure exist on disk.
    """
    missing_dirs = []
    for dir_name in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.is_dir():
            missing_dirs.append(dir_name)
    
    assert not missing_dirs, f"Missing required directories: {missing_dirs}"

def test_gitkeep_files_exist():
    """
    Integration test: Asserts that .gitkeep files exist in data directories
    to ensure they are tracked by git.
    """
    data_dirs = ["data/raw", "data/interim", "data/processed", "data/figures"]
    missing_gitkeeps = []
    
    for dir_name in data_dirs:
        dir_path = PROJECT_ROOT / dir_name
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            missing_gitkeeps.append(dir_name)
    
    assert not missing_gitkeeps, f"Missing .gitkeep in: {missing_gitkeeps}"

def test_code_directory_structure():
    """
    Contract test: Verifies the code directory exists and is a directory.
    """
    code_dir = PROJECT_ROOT / "code"
    assert code_dir.is_dir(), "The 'code' directory must exist"
    
    # Check for expected initial files (created by other tasks)
    expected_files = [
        "config.py",
        "data_model.py",
        "ingest.py",
        "preprocess.py",
        "analysis.py",
        "report.py"
    ]
    
    # We only check that the directory exists; specific files are created by other tasks
    # This test ensures the container exists.
    
def test_tests_directory_structure():
    """
    Contract test: Verifies the tests directory exists.
    """
    tests_dir = PROJECT_ROOT / "tests"
    assert tests_dir.is_dir(), "The 'tests' directory must exist"
