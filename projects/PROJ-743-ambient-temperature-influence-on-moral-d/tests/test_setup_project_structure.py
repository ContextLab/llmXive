"""
Unit tests for setup_project_structure.py
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import the module
# Assuming tests are run from the project root
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project_structure import ensure_directories

def test_ensure_directories_creates_all_required():
    """
    Test that ensure_directories creates all required directories.
    We run this in a temporary directory to avoid side effects.
    """
    # Create a temporary directory and change to it
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Call the function
            created = ensure_directories()
            
            # Verify all expected directories exist
            expected_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "results/figures",
                "results/logs",
                "results/stats",
                "tests"
            ]
            
            for expected in expected_dirs:
                path = Path(expected)
                assert path.exists(), f"Directory {expected} was not created"
                assert path.is_dir(), f"{expected} exists but is not a directory"
            
            # Verify the function returned the list of created paths
            assert len(created) == len(expected_dirs), f"Expected {len(expected_dirs)} dirs, got {len(created)}"
            
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

def test_ensure_directories_idempotent():
    """
    Test that running ensure_directories multiple times does not raise errors
    and does not duplicate directories.
    """
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Run once
            first_run = ensure_directories()
            
            # Run again
            second_run = ensure_directories()
            
            # Both runs should succeed and list the same number of directories
            assert len(first_run) == len(second_run)
            
            # Check that directories still exist
            expected_dirs = [
                "code", "data/raw", "data/processed",
                "results/figures", "results/logs", "results/stats", "tests"
            ]
            for d in expected_dirs:
                assert Path(d).exists()
        finally:
            os.chdir(original_cwd)
