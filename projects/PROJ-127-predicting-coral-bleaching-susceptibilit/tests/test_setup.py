"""
Test to verify that the project structure has been created correctly.
This test ensures that the required directories exist after running setup_project.py.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/models",
    "tests",
    "tests/unit",
    "tests/integration",
    "specs",
    "figures",
]

def test_project_structure_exists():
    """Verify that all required project directories exist."""
    root = Path(".")
    missing_dirs = []

    for dir_name in REQUIRED_DIRS:
        dir_path = root / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
        elif not dir_path.is_dir():
            missing_dirs.append(f"{dir_name} (not a directory)")

    if missing_dirs:
        pytest.fail(f"Missing required directories: {', '.join(missing_dirs)}")

def test_data_subdirectories_exist():
    """Verify that data subdirectories exist and are writable."""
    root = Path(".")
    data_dirs = ["data/raw", "data/processed", "data/models"]

    for dir_name in data_dirs:
        dir_path = root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"
        # Check writability by attempting to create a temporary file
        test_file = dir_path / ".test_write_permission"
        try:
            test_file.touch()
            test_file.unlink()
        except OSError as e:
            pytest.fail(f"Directory {dir_name} is not writable: {e}")