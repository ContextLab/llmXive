import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import setup_project
# This assumes the test is run from the project root or with appropriate PYTHONPATH
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project import main

def test_directory_structure_creation(tmp_path):
    """
    Test that setup_project creates the required directory structure.
    """
    # Change to the temporary directory to simulate the project root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Call the main function which creates the directories
        exit_code = main()
        
        # Verify the function returned 0 (success)
        assert exit_code == 0, "setup_project.main() should return 0 on success"
        
        # Define the expected directories relative to tmp_path
        expected_dirs = [
            "code",
            "tests",
            "data/raw",
            "data/generated",
            "data/results",
            "state/projects"
        ]
        
        # Verify each directory exists
        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} should exist after running setup_project"
            assert dir_path.is_dir(), f"{dir_path} should be a directory"
        
        # Verify the 'state/projects' nested structure specifically
        state_projects = tmp_path / "state" / "projects"
        assert state_projects.exists(), "state/projects should exist"
        assert state_projects.is_dir(), "state/projects should be a directory"

    finally:
        # Restore the original working directory
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """
    Test that running setup_project twice does not cause errors.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Run twice
        exit_code_1 = main()
        exit_code_2 = main()
        
        assert exit_code_1 == 0
        assert exit_code_2 == 0
        
        # Verify structure still exists
        expected_dirs = [
            "code",
            "tests",
            "data/raw",
            "data/generated",
            "data/results",
            "state/projects"
        ]
        
        for dir_name in expected_dirs:
            assert (tmp_path / dir_name).exists()
            
    finally:
        os.chdir(original_cwd)
