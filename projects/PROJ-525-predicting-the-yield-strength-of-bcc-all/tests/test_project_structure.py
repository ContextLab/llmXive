"""
Test for T001: Verify project structure creation.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, 'code')
from setup_project_structure import main

def test_project_structure_created():
    """Verify that the required directories are created."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Run the setup script
            result = main()
            
            # Verify return code
            assert result == 0, "Main function should return 0 on success"
            
            # Define expected directories
            expected_dirs = [
                "data/raw",
                "data/processed",
                "data/logs",
                "code",
                "tests",
                "reports",
                "state"
            ]
            
            # Verify each directory exists
            for dir_name in expected_dirs:
                dir_path = Path(tmpdir) / dir_name
                assert dir_path.exists(), f"Directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"
                
        finally:
            os.chdir(original_cwd)

def test_project_structure_idempotent():
    """Verify that running the script twice doesn't fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Run twice
            result1 = main()
            result2 = main()
            
            assert result1 == 0
            assert result2 == 0
            
        finally:
            os.chdir(original_cwd)
