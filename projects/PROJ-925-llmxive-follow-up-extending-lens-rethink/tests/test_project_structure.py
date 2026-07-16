"""
Test suite to verify the project directory structure was created correctly.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code/data",
    "code/tests",
    "code/utils",
    "code/models",
    "data/raw",
    "data/processed",
    "docs",
]

def test_required_directories_exist():
    """Verify that all required project directories exist."""
    base_path = Path(".")
    missing_dirs = []

    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing_dirs.append(dir_path)

    assert len(missing_dirs) == 0, f"The following directories are missing: {missing_dirs}"

def test_data_subdirectories_exist():
    """Verify that specific data subdirectories exist."""
    base_path = Path(".")
    data_dirs = ["data/raw", "data/processed"]

    for dir_path in data_dirs:
        full_path = base_path / dir_path
        assert full_path.exists() and full_path.is_dir(), f"Missing data directory: {dir_path}"

def test_code_subdirectories_exist():
    """Verify that specific code subdirectories exist."""
    base_path = Path(".")
    code_dirs = ["code/data", "code/tests", "code/utils", "code/models"]

    for dir_path in code_dirs:
        full_path = base_path / dir_path
        assert full_path.exists() and full_path.is_dir(), f"Missing code directory: {dir_path}"