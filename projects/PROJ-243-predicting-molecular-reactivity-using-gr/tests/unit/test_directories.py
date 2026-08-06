"""
Unit tests to verify that the required project directory structure exists.
These tests ensure that T001a, T001b, T001c, and T002 prerequisites are met.
"""
import os
import pytest
from pathlib import Path

# Root of the project (assumed to be the directory containing this test file's parent)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/assets",
    "code",
    "artifacts",
    "tests",
]

def test_required_directories_exist():
    """
    Asserts that all required directories defined in the project setup tasks
    (T001a, T001b, T001c, T002) exist on the filesystem.
    """
    missing_dirs = []
    for dir_name in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_name
        if not full_path.exists():
            missing_dirs.append(dir_name)
        elif not full_path.is_dir():
            missing_dirs.append(f"{dir_name} (exists but is not a directory)")

    assert len(missing_dirs) == 0, f"The following required directories are missing: {missing_dirs}"

def test_data_processed_has_placeholder():
    """
    Specific check for T001b: Ensure data/processed is tracked (has .gitkeep).
    """
    processed_dir = PROJECT_ROOT / "data" / "processed"
    assert processed_dir.exists(), "data/processed directory does not exist."
    assert processed_dir.is_dir(), "data/processed is not a directory."
    
    # Check for the .gitkeep file to ensure the empty directory is committed
    gitkeep = processed_dir / ".gitkeep"
    assert gitkeep.exists(), "data/processed/.gitkeep is missing. Empty directories must be tracked via a placeholder."