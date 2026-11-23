"""
Test to verify that the directory structure created by T001a exists.
This test ensures the implementation of T001a is valid.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/reports",
    "tests",
    "artifacts"
]

def test_directory_structure_exists():
    """
    Verifies that all required directories from T001a exist in the project root.
    """
    root = Path.cwd()
    missing_dirs = []

    for dir_name in REQUIRED_DIRS:
        full_path = root / dir_name
        if not full_path.exists():
            missing_dirs.append(dir_name)
        elif not full_path.is_dir():
            missing_dirs.append(f"{dir_name} (is not a directory)")

    assert len(missing_dirs) == 0, f"Missing directories: {missing_dirs}"