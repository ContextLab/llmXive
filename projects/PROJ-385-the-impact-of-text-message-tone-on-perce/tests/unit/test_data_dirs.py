"""
Unit tests for data directory creation (T005).
"""
import os
import pytest
from pathlib import Path
from config import get_project_root
from setup_data_dirs import main

def test_data_directories_exist():
    """Verify that data/raw, data/processed, and data/consent directories exist."""
    project_root = get_project_root()
    data_dir = project_root / "data"

    required_dirs = ["raw", "processed", "consent"]

    for subdir in required_dirs:
        dir_path = data_dir / subdir
        assert dir_path.exists(), f"Directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_gitkeep_files_exist():
    """Verify that .gitkeep files exist in data directories."""
    project_root = get_project_root()
    data_dir = project_root / "data"

    # Check main data directory
    assert (data_dir / ".gitkeep").exists(), "Missing .gitkeep in data/"

    # Check subdirectories
    required_dirs = ["raw", "processed", "consent"]
    for subdir in required_dirs:
        dir_path = data_dir / subdir
        gitkeep_path = dir_path / ".gitkeep"
        assert gitkeep_path.exists(), f"Missing .gitkeep in {dir_path}"

def test_setup_data_dirs_script_runs():
    """Test that the setup script runs without errors and creates directories."""
    # This test ensures the script can be executed
    # The directories should already exist from previous runs, but the script should handle it gracefully
    main()  # Should not raise an exception
    test_data_directories_exist()  # Verify they exist after running