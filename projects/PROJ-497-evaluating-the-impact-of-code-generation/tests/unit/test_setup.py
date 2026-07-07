"""
Unit tests for project structure initialization.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "data/generated",
    "results",
    "results/figures",
    "state",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "specs",
    "docs",
]

def get_project_root():
    """Get the project root directory (parent of tests)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_directory_exists(dir_name):
    """Assert that all required directories exist."""
    root = get_project_root()
    full_path = os.path.join(root, dir_name)
    assert os.path.exists(full_path), f"Directory {dir_name} does not exist"
    assert os.path.isdir(full_path), f"Path {dir_name} is not a directory"