import os
import pytest
from pathlib import Path

def test_directory_exists():
    """
    Verify that the required project directory structure exists.
    This test checks for the presence of src, tests, contracts, data, and analysis directories.
    """
    base_path = Path(__file__).resolve().parents[3]  # Navigate to project root (code/)
    
    required_dirs = [
        "src",
        "tests",
        "contracts",
        "data",
        "analysis"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"Directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

def test_config_files_exist():
    """
    Verify that essential configuration files exist in the project root.
    """
    base_path = Path(__file__).resolve().parents[3]  # Navigate to project root (code/)
    
    required_files = [
        "requirements.txt",
        "pyproject.toml"
    ]
    
    for file_name in required_files:
        file_path = base_path / file_name
        assert file_path.exists(), f"File {file_path} does not exist."