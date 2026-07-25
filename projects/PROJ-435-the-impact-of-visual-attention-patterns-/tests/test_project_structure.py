"""
Test for Task T001: Verify project structure exists.
This test ensures that the required directories for the project
have been created as per the implementation plan.
"""
import os
import pytest
from pathlib import Path

# Determine the root directory (two levels up from this test file)
ROOT_DIR = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/derived",
    "data/processed",
    "tests",
    "state"
]

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_directory_exists(dir_name):
    """Verify that each required directory exists."""
    target_path = ROOT_DIR / dir_name
    assert target_path.exists(), f"Directory {dir_name} does not exist at {target_path}"
    assert target_path.is_dir(), f"{dir_name} exists but is not a directory"

def test_data_subdirectories_exist():
    """Verify that data subdirectories are present."""
    data_path = ROOT_DIR / "data"
    assert data_path.exists() and data_path.is_dir(), "data directory missing"
    
    subdirs = ["raw", "derived", "processed"]
    for subdir in subdirs:
        subdir_path = data_path / subdir
        assert subdir_path.exists() and subdir_path.is_dir(), f"data/{subdir} missing"
