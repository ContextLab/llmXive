import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from create_structure import main

def test_directory_structure_creation():
    """
    Test that the main() function creates the required directory structure.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the structure creation
            exit_code = main()
            
            # Verify exit code is 0 (success)
            assert exit_code == 0, "main() should return 0 on success"
            
            # Define expected directories
            expected_dirs = [
                "code",
                "data/raw",
                "data/interim",
                "data/processed",
                "tests",
                "reports",
                "docs",
                ".github/workflows",
                "specs"
            ]
            
            # Verify each directory exists
            for dir_name in expected_dirs:
                dir_path = Path(tmp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"
            
            # Verify .gitkeep files exist in data subdirectories
            data_subdirs = ["data/raw", "data/interim", "data/processed"]
            for dir_name in data_subdirs:
                gitkeep_path = Path(tmp_dir) / dir_name / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep should exist in {dir_name}"
                
        finally:
            os.chdir(original_cwd)

def test_idempotency():
    """
    Test that running main() multiple times doesn't cause errors.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run twice
            exit_code_1 = main()
            exit_code_2 = main()
            
            assert exit_code_1 == 0
            assert exit_code_2 == 0
            
        finally:
            os.chdir(original_cwd)
