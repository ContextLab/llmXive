"""
Test suite to verify the project directory structure exists.
This ensures T001, T002, and T003 requirements are met.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "data",
    "data/defects4j",
    "code",
    "code/utils",
    "code/models",
    "explanations",
    "state",
    "tests",
]

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(dir_path: str) -> None:
    """Assert that a required directory exists."""
    path = Path(dir_path)
    assert path.exists(), f"Directory '{dir_path}' does not exist."
    assert path.is_dir(), f"'{dir_path}' exists but is not a directory."