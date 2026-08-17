"""
Integration tests for the directory setup task (T001a).
Verifies that the required project structure exists.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "data/analysis",
    "tests",
    "contracts",
    "state"
]

def test_directory_structure_exists():
    """Assert that all required directories exist in the project root."""
    base_path = Path(".")
    missing_dirs = []
    
    for dir_name in REQUIRED_DIRS:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
        elif not dir_path.is_dir():
            missing_dirs.append(f"{dir_name} (not a directory)")
    
    assert len(missing_dirs) == 0, f"Missing or invalid directories: {missing_dirs}"

def test_data_subdirectories_exist():
    """Assert that data subdirectories are present."""
    base_path = Path(".")
    data_subdirs = ["data/raw", "data/processed", "data/analysis"]
    
    for subdir in data_subdirs:
        dir_path = base_path / subdir
        assert dir_path.exists(), f"Data subdirectory missing: {subdir}"
        assert dir_path.is_dir(), f"Data subdirectory is not a directory: {subdir}"