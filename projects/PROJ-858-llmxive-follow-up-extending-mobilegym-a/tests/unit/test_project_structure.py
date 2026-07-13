"""
Unit tests to verify the project structure was created correctly.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code",
    "code/scheduler",
    "code/training",
    "code/analysis",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/validation",
    "tests/unit",
    "tests/integration",
    "contracts",
]

@pytest.mark.parametrize("directory", REQUIRED_DIRS)
def test_directory_exists(directory: str):
    """Test that each required directory exists."""
    assert os.path.isdir(directory), f"Directory {directory} does not exist"

def test_all_directories_exist():
    """Test that all required directories exist."""
    missing_dirs = [d for d in REQUIRED_DIRS if not os.path.isdir(d)]
    assert not missing_dirs, f"Missing directories: {missing_dirs}"
