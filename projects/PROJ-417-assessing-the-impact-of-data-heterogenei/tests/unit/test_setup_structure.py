"""
Unit tests for project structure initialization.
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from code.setup_structure import main


def test_structure_creation():
    """
    Test that the main() function creates the required directories.
    
    This test runs in a temporary directory to avoid polluting the actual
    project structure during testing.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            # Change to the temporary directory
            os.chdir(temp_dir)
            
            # Run the setup script
            main()
            
            # Define expected directories
            expected_dirs = [
                "code/simulation",
                "code/analysis",
                "code/visualization",
                "code/reporting",
                "data/raw",
                "data/processed",
                "data/results",
                "tests/unit",
                "tests/integration",
                "contracts"
            ]
            
            # Verify each directory exists
            project_root = Path(temp_dir)
            for dir_path in expected_dirs:
                full_path = project_root / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory"
            
            # If we get here, all assertions passed
            print("All required directories were created successfully.")
            
        finally:
            # Restore original working directory
            os.chdir(original_cwd)


def test_idempotency():
    """
    Test that running the script twice doesn't cause errors.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Run twice
            main()
            main()
            
            # Verify structure still exists
            expected_dirs = [
                "code/simulation",
                "data/raw",
                "contracts"
            ]
            
            project_root = Path(temp_dir)
            for dir_path in expected_dirs:
                assert (project_root / dir_path).exists()
            
        finally:
            os.chdir(original_cwd)
