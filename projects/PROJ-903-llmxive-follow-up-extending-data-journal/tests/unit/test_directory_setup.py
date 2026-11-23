"""
Unit tests to verify the creation of required data directories.
"""
import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    Verify that the required data directories exist after setup.
    """
    project_root = Path("projects/PROJ-903-llmxive-follow-up-extending-data-journal")
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "output"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"

def test_gitkeep_files_exist():
    """
    Verify that .gitkeep files exist in the data directories to ensure git tracking.
    """
    project_root = Path("projects/PROJ-903-llmxive-follow-up-extending-data-journal")
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "output"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        gitkeep = full_path / ".gitkeep"
        assert gitkeep.exists(), f".gitkeep file missing in {full_path}"
        assert gitkeep.is_file(), f"{gitkeep} is not a file"