"""
Test suite to verify the project directory structure exists as required by T001a and T004.

This test ensures:
1. Root directories (code, data, tests, docs) exist.
2. Data subdirectories (raw, processed) exist.
3. Contracts directory exists.
4. Placeholder files exist where expected.
"""
import os
from pathlib import Path
import pytest

BASE_PATH = Path.cwd()

required_directories = [
    "code",
    "data",
    "tests",
    "docs",
    "data/raw",
    "data/processed",
    "contracts",
    "figures",
    "state",
    "state/projects"
]

required_files = [
    "code/__init__.py",
    "tests/__init__.py",
    "data/__init__.py",
    "docs/README.md"
]

@pytest.mark.parametrize("dir_name", required_directories)
def test_directory_exists(dir_name):
    """Assert that a specific required directory exists."""
    full_path = BASE_PATH / dir_name
    assert full_path.exists(), f"Directory '{dir_name}' does not exist."
    assert full_path.is_dir(), f"'{dir_name}' exists but is not a directory."

@pytest.mark.parametrize("file_name", required_files)
def test_placeholder_file_exists(file_name):
    """Assert that a specific required placeholder file exists."""
    full_path = BASE_PATH / file_name
    assert full_path.exists(), f"File '{file_name}' does not exist."