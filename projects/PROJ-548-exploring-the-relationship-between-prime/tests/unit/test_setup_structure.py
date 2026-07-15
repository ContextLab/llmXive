"""
Unit tests to verify the project structure initialization.
These tests check that the expected directories and __init__.py files exist.
"""
import os
import pytest
from pathlib import Path

# Define the expected structure relative to the project root
# We assume tests are run from the project root
EXPECTED_DIRS = [
    "code/data",
    "code/analysis",
    "code/utils",
    "code/cli",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
    "data/results",
    "results",
    "state"
]

PKG_DIRS = [
    "code/data",
    "code/analysis",
    "code/utils",
    "code/cli",
    "tests/unit",
    "tests/integration"
]

def get_project_root():
    """Determine the project root (parent of tests/)."""
    return Path(__file__).parent.parent.parent

@pytest.fixture
def root_path():
    return get_project_root()

def test_directories_exist(root_path):
    """Verify all required directories exist."""
    for dir_path in EXPECTED_DIRS:
        full_path = root_path / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist."
        assert full_path.is_dir(), f"{dir_path} exists but is not a directory."

def test_init_files_exist(root_path):
    """Verify __init__.py exists in all code/ and tests/ subdirectories."""
    for dir_path in PKG_DIRS:
        full_path = root_path / dir_path
        init_file = full_path / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {dir_path}."
        assert init_file.is_file(), f"{init_file} is not a file."

def test_data_directories_writable(root_path):
    """Verify data directories are writable (basic sanity check)."""
    data_dirs = ["data/raw", "data/processed", "data/results"]
    for dir_path in data_dirs:
        full_path = root_path / dir_path
        test_file = full_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            pytest.fail(f"Directory {dir_path} is not writable: {e}")