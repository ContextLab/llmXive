"""
Unit tests to verify that the project structure created by T001 exists.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code/src/generators",
    "code/src/estimators",
    "code/src/metrics",
    "code/src/viz",
    "code/tests/unit",
    "code/tests/integration",
    "data",
    "results",
    "contracts",
    "config"
]

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(dir_path):
    """Assert that each required directory exists."""
    assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist."

def test_all_directories_exist():
    """Assert that all required directories exist in one go."""
    missing = [d for d in REQUIRED_DIRS if not os.path.isdir(d)]
    assert not missing, f"The following directories are missing: {missing}"