"""
Unit test for T001: Verify project structure creation.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the main logic to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_project_structure import main

def test_project_structure_creation():
    """
    Assert that the required directories are created when the script runs.
    """
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the setup script
            main()
            
            # Define expected directories relative to the temp root
            expected_dirs = [
                "code/utils",
                "code/tests/unit",
                "code/tests/integration",
                "data/raw",
                "data/networks",
                "data/transport",
                "data/analysis",
                "plots",
                "state/projects",
            ]
            
            # Assert each directory exists
            for dir_path in expected_dirs:
                full_path = Path(tmp_dir) / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created."
                assert full_path.is_dir(), f"Path {dir_path} exists but is not a directory."
        
        finally:
            os.chdir(original_cwd)