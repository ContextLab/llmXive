"""
Unit tests for the directory setup functionality.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_dirs import create_directory_structure


def test_create_directory_structure():
    """
    Test that create_directory_structure creates all required directories.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Call the function
            paths = create_directory_structure()
            
            # Verify all expected directories exist
            expected_dirs = [
                "code",
                "tests",
                "contracts",
                "data/raw",
                "data/processed",
                "data/results",
                "data/logs",
            ]
            
            for dir_name in expected_dirs:
                dir_path = Path(temp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
            
            # Verify the returned list contains all paths
            assert len(paths) == len(expected_dirs)
            for expected_dir in expected_dirs:
                assert any(expected_dir in p for p in paths), f"Path for {expected_dir} not in returned list"
                
        finally:
            os.chdir(original_cwd)


def test_create_directory_structure_idempotent():
    """
    Test that running create_directory_structure multiple times is safe.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Run twice
            paths1 = create_directory_structure()
            paths2 = create_directory_structure()
            
            # Both runs should succeed and produce same structure
            assert len(paths1) == len(paths2)
            
            # Verify all directories still exist
            expected_dirs = [
                "code",
                "tests",
                "contracts",
                "data/raw",
                "data/processed",
                "data/results",
                "data/logs",
            ]
            
            for dir_name in expected_dirs:
                dir_path = Path(temp_dir) / dir_name
                assert dir_path.exists()
                
        finally:
            os.chdir(original_cwd)