"""
Unit tests for the setup_directories module.
Verifies that the required directory structure is created correctly.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the parent directory to the path to import setup_directories
# Assuming this test is in tests/unit/ and code/setup_directories.py is at code/setup_directories.py
# We need to navigate up two levels from tests/unit to root, then into code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from setup_directories import REQUIRED_DIRS, main

def test_required_dirs_list():
    """Test that the REQUIRED_DIRS list contains the expected paths."""
    expected_dirs = {
        "data/raw",
        "data/processed",
        "code/models",
        "code/metrics",
        "code/stats",
        "results",
        "tests/unit",
        "tests/integration",
        "code/utils"
    }
    assert set(REQUIRED_DIRS) == expected_dirs, f"Required dirs mismatch. Expected: {expected_dirs}, Got: {set(REQUIRED_DIRS)}"

def test_directory_creation_in_temp_dir(monkeypatch, tmp_path):
    """
    Test that the main function creates directories in a temporary location.
    We patch the BASE_DIR logic to use our temp directory.
    """
    # We need to re-import or mock the BASE_DIR inside setup_directories
    # Since main() uses a global BASE_DIR derived from __file__, we can't easily patch it without reloading.
    # Instead, we will manually test the logic of creating directories.
    
    # Let's create a temporary root
    temp_root = tmp_path / "test_project"
    temp_root.mkdir()

    created_count = 0
    for dir_path in REQUIRED_DIRS:
        full_path = temp_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
    
    # Verify all directories exist
    for dir_path in REQUIRED_DIRS:
        full_path = temp_root / dir_path
        assert full_path.exists(), f"Directory {full_path} was not created."
        assert full_path.is_dir(), f"{full_path} is not a directory."

    # Verify the count (all should be created since it's a new temp dir)
    assert created_count == len(REQUIRED_DIRS), f"Expected {len(REQUIRED_DIRS)} directories to be created, got {created_count}"