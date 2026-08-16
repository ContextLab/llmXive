"""
Unit tests for the project_setup module.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from project_setup import create_project_structure


def test_create_project_structure_creates_directories():
    """
    Test that create_project_structure creates the required directories.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the function
            result = create_project_structure()
            
            # Verify the result list contains paths
            assert len(result) > 0, "Expected a non-empty list of created directories"
            
            # Verify specific required directories exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/survey",
                "tests"
            ]
            
            for dir_name in required_dirs:
                expected_path = Path(tmp_dir) / dir_name
                assert expected_path.exists(), f"Required directory missing: {expected_path}"
                assert expected_path.is_dir(), f"Path is not a directory: {expected_path}"
            
            # Verify .gitkeep files were created
            for dir_name in required_dirs:
                gitkeep_path = Path(tmp_dir) / dir_name / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep missing in: {dir_name}"
                
        finally:
            os.chdir(original_cwd)


def test_create_project_structure_idempotent():
    """
    Test that running the function twice does not raise errors.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run once
            create_project_structure()
            
            # Run again - should not raise
            result2 = create_project_structure()
            
            # Should still return a list of existing directories
            assert len(result2) > 0
            
        finally:
            os.chdir(original_cwd)
