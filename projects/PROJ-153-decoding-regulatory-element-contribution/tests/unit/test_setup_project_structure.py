import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# We need to adjust the path to import correctly if running from tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_project_structure import create_directories

def test_directory_creation():
    """Test that the create_directories function creates the expected structure."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the function
            create_directories()
            
            # Verify directories exist
            expected_dirs = [
                "code",
                "tests/unit",
                "tests/integration",
                "tests/contract",
                "data/raw",
                "data/processed",
                "data/intermediate",
                "results",
                "figures",
                "specs"
            ]
            
            for dir_name in expected_dirs:
                full_path = Path(dir_name)
                assert full_path.exists(), f"Directory {full_path} was not created."
                assert full_path.is_dir(), f"{full_path} exists but is not a directory."
                
        finally:
            os.chdir(original_cwd)

def test_idempotency():
    """Test that running the function twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run twice
            create_directories()
            create_directories()
            
            # Should still exist
            assert Path("code").exists()
            assert Path("results").exists()
            
        finally:
            os.chdir(original_cwd)