import os
import pytest
from pathlib import Path
from config import get_raw_data_dir, get_processed_data_dir, get_consent_dir, get_results_dir, get_mock_data_dir

def test_data_directories_exist():
    """
    Verify that the required data sub-directories exist.
    This test corresponds to T005.
    """
    dirs = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
        get_results_dir(),
        get_mock_data_dir()
    ]
    
    for dir_path in dirs:
        assert dir_path.exists(), f"Directory does not exist: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_gitkeep_files_exist():
    """
    Verify that each required data sub-directory contains a .gitkeep file.
    This test corresponds to T005.
    """
    dirs = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
        get_results_dir(),
        get_mock_data_dir()
    ]
    
    for dir_path in dirs:
        gitkeep_path = dir_path / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep file missing in {dir_path}"
        assert gitkeep_path.is_file(), f".gitkeep is not a file in {dir_path}"
