"""
Unit tests for the project directory initialization logic.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We need to ensure the code directory is in the path if running from tests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import initialize_project_structure


def test_initialize_project_structure_creates_dirs():
    """
    Verify that initialize_project_structure creates the required directories.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Call the function
            initialize_project_structure()
            
            # Verify directories exist
            required_dirs = [
                "code",
                "tests",
                "data/raw",
                "data/processed",
                "results"
            ]
            
            for dir_name in required_dirs:
                dir_path = Path(tmp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
                
            # Verify nested structure (data/raw and data/processed)
            assert (Path(tmp_dir) / "data" / "raw").exists()
            assert (Path(tmp_dir) / "data" / "processed").exists()
            
        finally:
            os.chdir(original_cwd)

def test_initialize_project_structure_idempotent():
    """
    Verify that running the function twice does not raise errors.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run once
            initialize_project_structure()
            
            # Run again - should not raise
            initialize_project_structure()
            
            # Verify structure is intact
            assert (Path(tmp_dir) / "code").exists()
            assert (Path(tmp_dir) / "results").exists()
            
        finally:
            os.chdir(original_cwd)