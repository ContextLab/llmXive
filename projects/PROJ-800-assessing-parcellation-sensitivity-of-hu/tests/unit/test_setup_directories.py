"""
Unit tests for the setup_directories script functionality.

Verifies that the directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path to import the module
# We assume this test runs from the project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import main

def test_directory_creation_structure():
    """Test that the required directories are created in the correct structure."""
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as temp_root:
        temp_path = Path(temp_root)
        
        # Temporarily change the working directory
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_path)
            
            # Run the main function (it will use current dir as root)
            # We need to mock the print statements or capture them, 
            # but for this test we just care about side effects.
            # Since main() doesn't return anything, we just call it.
            # However, main() uses Path.cwd(), which is now temp_path.
            main()
            
            # Verify directories exist
            required_dirs = [
                "data/raw",
                "data/processed",
                "data/results",
                "code",
                "tests"
            ]
            
            for dir_name in required_dirs:
                dir_path = temp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
                
            # Verify nested structure
            assert (temp_path / "data/raw").exists()
            assert (temp_path / "data/processed").exists()
            assert (temp_path / "data/results").exists()
            
        finally:
            os.chdir(original_cwd)

def test_idempotency():
    """Test that running the script multiple times does not cause errors."""
    with tempfile.TemporaryDirectory() as temp_root:
        temp_path = Path(temp_root)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_path)
            
            # Run twice
            main()
            main()
            
            # Verify directories still exist and are valid
            required_dirs = ["data/raw", "data/processed", "data/results", "code", "tests"]
            for dir_name in required_dirs:
                assert (temp_path / dir_name).exists()
                
        finally:
            os.chdir(original_cwd)