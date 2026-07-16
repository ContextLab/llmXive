"""
Unit tests for code/utils/directories.py
"""
import pytest
from pathlib import Path
import shutil
import tempfile
import os

# We need to test the logic in isolation, but the module uses a fixed relative path
# to find the project root. To test this robustly, we will mock the _PROJECT_ROOT
# or ensure the test runs in an environment where the relative path logic holds.
# However, since the module calculates _PROJECT_ROOT at import time based on __file__,
# and we are running tests from the project root or via pytest, we need to be careful.

# Strategy: 
# 1. Import the module.
# 2. Verify that the directories listed in DATA_DIRS exist after calling the function.
# 3. Verify that the function returns the correct Path objects.

# Note: The actual implementation uses Path(__file__).resolve().parent.parent.parent
# to find the root. This assumes the file is at code/utils/directories.py.
# If the test runner is run from the project root, this should align with the actual
# data/ directory.

from utils.directories import ensure_data_directories, DATA_DIRS, _PROJECT_ROOT

def test_ensure_data_directories_creates_missing_dirs():
    """
    Test that ensure_data_directories creates directories that do not exist.
    """
    # Identify a target directory to test (e.g., data/results)
    # We will temporarily remove it to test creation.
    # Note: We must be careful not to delete data that might be in use by other tests
    # if they run in parallel. We assume a clean state or that we can safely remove
    # the specific target for this test.
    
    target_rel = "data/results"
    target_path = _PROJECT_ROOT / target_rel
    
    # Backup if exists, or just ensure it's gone for the test
    was_existing = target_path.exists()
    if was_existing:
        # We can't easily delete a directory if it's not empty, but for a fresh run
        # it might be empty. If it's not empty, we skip the deletion and just test
        # that the function handles existing dirs.
        # To be safe, we'll just test the 'exist_ok' behavior if we can't delete.
        try:
            shutil.rmtree(target_path)
        except OSError:
            # If we can't remove it (e.g., not empty), we rely on the exist_ok test
            pass
    
    # Call the function
    result_dirs = ensure_data_directories()
    
    # Verify the target directory now exists
    assert target_path.exists(), f"Directory {target_path} was not created."
    assert target_path.is_dir(), f"{target_path} exists but is not a directory."
    
    # Verify it is in the returned list
    assert target_path in result_dirs, "Created directory not in return list."

def test_ensure_data_directories_handles_existing_dirs():
    """
    Test that ensure_data_directories does not fail if directories already exist.
    """
    # Ensure at least one directory exists
    target_rel = "data/raw"
    target_path = _PROJECT_ROOT / target_rel
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Call the function
    result_dirs = ensure_data_directories()
    
    # Should succeed and return the path
    assert target_path in result_dirs
    assert target_path.exists()

def test_ensure_data_directories_returns_correct_paths():
    """
    Test that the function returns a list of Path objects corresponding to DATA_DIRS.
    """
    result_dirs = ensure_data_directories()
    
    assert isinstance(result_dirs, list)
    assert len(result_dirs) == len(DATA_DIRS)
    
    for rel_path in DATA_DIRS:
        expected_path = _PROJECT_ROOT / rel_path
        assert expected_path in result_dirs, f"Missing expected path: {expected_path}"

def test_data_dirs_constant():
    """
    Verify the DATA_DIRS constant contains the expected relative paths.
    """
    expected = ["data/raw", "data/processed", "data/results"]
    assert DATA_DIRS == expected, f"DATA_DIRS mismatch: {DATA_DIRS} != {expected}"