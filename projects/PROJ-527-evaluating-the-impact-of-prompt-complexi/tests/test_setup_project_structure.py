"""
Tests for Task T002: Project Structure Creation.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import the module
# Assuming tests are in tests/ and code is in code/
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project_structure import create_project_structure

def test_creates_required_directories():
    """
    Verify that create_project_structure creates the required directories.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Call the function
            create_project_structure()
            
            # Verify directories exist
            required_dirs = [
                "code",
                "tests",
                "data/raw",
                "data/processed",
                "data/results",
                "state/projects",
            ]
            
            for dir_path in required_dirs:
                full_path = Path(temp_dir) / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created."
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory."
                
        finally:
            os.chdir(original_cwd)

def test_handles_existing_directories():
    """
    Verify that the function does not fail if directories already exist.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Pre-create some directories
            Path(temp_dir, "code").mkdir()
            Path(temp_dir, "data", "raw").mkdir(parents=True)
            
            # Call the function
            # It should not raise an exception
            create_project_structure()
            
            # Verify they still exist
            assert Path(temp_dir, "code").exists()
            assert Path(temp_dir, "data", "raw").exists()
            
        finally:
            os.chdir(original_cwd)
