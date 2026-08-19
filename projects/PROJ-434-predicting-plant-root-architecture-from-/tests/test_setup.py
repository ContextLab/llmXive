"""
Test to verify that the required directory structure exists.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "data/logs",
    "tests",
    "artifacts",
    "figures"
]

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_directory_exists(dir_name):
    """Assert that each required directory exists."""
    path = Path(dir_name)
    assert path.exists(), f"Directory {dir_name} does not exist."
    assert path.is_dir(), f"Path {dir_name} is not a directory."

def test_data_subdirectories():
    """Assert that data subdirectories exist."""
    assert Path("data/raw").exists()
    assert Path("data/processed").exists()
    assert Path("data/logs").exists()
