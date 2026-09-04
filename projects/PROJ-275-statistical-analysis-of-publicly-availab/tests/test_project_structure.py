import os
import pytest
from pathlib import Path

def test_project_directories_exist():
    """
    Verify that the required project directories exist.
    This test ensures T001 has been successfully completed.
    """
    base_dir = Path.cwd()
    
    required_dirs = [
        "code",
        "code/tests",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "results",
        "results/figures",
        "specs",
        "specs/001-sentiment-revenue-lag-analysis",
        "specs/001-sentiment-revenue-lag-analysis/contracts",
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            missing_dirs.append(dir_name)
    
    assert len(missing_dirs) == 0, f"Missing required directories: {missing_dirs}"

def test_placeholder_files_exist():
    """
    Verify that placeholder files exist in data directories to prevent them from being empty.
    """
    base_dir = Path.cwd()
    
    required_files = [
        "data/logs/.gitkeep",
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "results/figures/.gitkeep",
        "specs/001-sentiment-revenue-lag-analysis/contracts/.gitkeep",
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = base_dir / file_name
        if not file_path.exists() or not file_path.is_file():
            missing_files.append(file_name)
    
    assert len(missing_files) == 0, f"Missing required placeholder files: {missing_files}"

def test_code_directory_is_not_empty():
    """
    Verify that the code directory contains at least some Python files.
    """
    base_dir = Path.cwd()
    code_dir = base_dir / "code"
    
    py_files = list(code_dir.glob("*.py"))
    # We expect at least the setup script and potentially others
    assert len(py_files) > 0, "The code directory should contain at least one Python file."