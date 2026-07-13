"""
Unit tests to verify the project structure was created correctly.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code/data",
    "code/models",
    "code/analysis",
    "code/utils",
    "data/raw",
    "data/processed",
    "tests/unit",
    "tests/integration"
]

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(dir_path):
    """Assert that a required directory exists."""
    assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist."

def test_all_directories_exist():
    """Assert that all required directories exist."""
    missing = [d for d in REQUIRED_DIRS if not os.path.isdir(d)]
    assert not missing, f"The following directories are missing: {missing}"