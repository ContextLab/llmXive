"""
Tests for the setup_dirs.py script.

Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# Since setup_dirs.py is in code/, we need to adjust path or import accordingly.
# Assuming the test runner is set up to add 'code' to sys.path or we import relative to root.
# For this test, we will simulate the environment by changing to a temp directory.

def test_directory_creation():
    """Test that main() creates the required directories."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Import here to ensure it uses the current working directory logic if any
            # We need to import from code.setup_dirs
            import sys
            sys.path.insert(0, os.path.join(tmp_dir, "..")) # Assuming code is sibling? 
            # Actually, the script is at code/setup_dirs.py. 
            # Let's import the module directly by manipulating path relative to the file location.
            
            # Better approach: Copy the script content logic or import the specific file
            # Since we are testing the behavior, let's just verify the paths created.
            
            # Re-importing logic:
            # The task creates code/setup_dirs.py. We need to run it.
            # We will import the main function by adding the 'code' directory to path if it exists,
            # but in a temp dir it might not.
            # Let's assume the project structure is:
            # root/
            #   code/
            #     setup_dirs.py
            #   tests/
            #     test_setup_dirs.py
            
            # We will create the 'code' folder in temp and copy the script logic?
            # No, the test should run against the actual file if possible, or mock the creation.
            # Given the constraint "Implement the task for real", the file code/setup_dirs.py exists in the artifact.
            # The test should verify that running it creates the dirs.
            
            # Let's set up the temp structure to match the project
            code_dir = Path(tmp_dir) / "code"
            code_dir.mkdir()
            tests_dir = Path(tmp_dir) / "tests"
            tests_dir.mkdir()
            
            # Add code to path
            sys.path.insert(0, str(code_dir))
            
            # Import the main function
            from setup_dirs import main
            
            # Define expected directories
            expected_dirs = [
                "src",
                "tests", # This already exists in our temp setup, but the script should handle it
                "data/raw",
                "data/processed",
                "models",
                "templates"
            ]
            
            # Run the function
            result = main()
            
            assert result == 0, "main() should return 0 on success"
            
            # Verify directories exist
            for dir_name in expected_dirs:
                dir_path = Path(tmp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"Path {dir_path} exists but is not a directory"
                
        finally:
            os.chdir(original_cwd)
            # Cleanup sys.path
            if str(code_dir) in sys.path:
                sys.path.remove(str(code_dir))

def test_nested_directory_creation():
    """Test that nested directories (e.g., data/raw) are created with parents=True."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            code_dir = Path(tmp_dir) / "code"
            code_dir.mkdir()
            sys.path.insert(0, str(code_dir))
            
            from setup_dirs import main
            
            # Ensure data directory doesn't exist yet
            data_dir = Path(tmp_dir) / "data"
            assert not data_dir.exists()
            
            main()
            
            # Check nested
            assert (Path(tmp_dir) / "data" / "raw").exists()
            assert (Path(tmp_dir) / "data" / "processed").exists()
            
        finally:
            os.chdir(original_cwd)
            if str(code_dir) in sys.path:
                sys.path.remove(str(code_dir))