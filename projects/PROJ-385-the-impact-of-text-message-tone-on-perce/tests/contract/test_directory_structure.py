"""
Contract tests to verify that the data directory structure is correctly created.
"""
import os
import pytest
from pathlib import Path

from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir
from setup_data_dirs import create_directory_structure


def test_create_directory_structure():
    """
    Test that create_directory_structure() creates the required directories
    and populates them with .gitkeep files.
    """
    project_root = get_project_root()
    directories = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir()
    ]

    # Ensure directories exist (run the creation function if they don't)
    for dir_path in directories:
        if not dir_path.is_absolute():
            dir_path = project_root / dir_path
        dir_path.mkdir(parents=True, exist_ok=True)

    # Verify each directory exists and contains .gitkeep
    for dir_path in directories:
        if not dir_path.is_absolute():
            dir_path = project_root / dir_path

        assert dir_path.exists(), f"Directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"{dir_path} is not a directory."

        gitkeep_path = dir_path / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep file missing in {dir_path}"
        assert gitkeep_path.is_file(), f".gitkeep in {dir_path} is not a file."


def test_setup_data_dirs_integration():
    """
    Integration test: Run the setup script and verify the result.
    """
    # Run the creation function
    success = create_directory_structure()
    assert success, "create_directory_structure() returned False."

    project_root = get_project_root()
    directories = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir()
    ]

    for dir_path in directories:
        if not dir_path.is_absolute():
            dir_path = project_root / dir_path

        assert dir_path.exists(), f"Directory {dir_path} missing after setup."
        assert (dir_path / ".gitkeep").exists(), f".gitkeep missing in {dir_path} after setup."