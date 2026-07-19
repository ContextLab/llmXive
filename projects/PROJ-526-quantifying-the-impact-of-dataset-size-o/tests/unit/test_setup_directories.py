import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import create_directories

def test_create_directories_structure():
    """
    Verifies that create_directories creates the expected subdirectories
    relative to a temporary root.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Call the function
            count = create_directories()
            
            # Verify the directories exist
            expected_dirs = [
                "data/raw",
                "data/processed",
                "state",
                "docs",
                "tests/contract",
                "tests/unit",
                "tests/integration",
            ]
            
            for dir_path in expected_dirs:
                full_path = Path(tmp_dir) / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created."
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory."
            
            # Verify count (all should be created since it's a fresh temp dir)
            assert count == len(expected_dirs), f"Expected {len(expected_dirs)} dirs, got {count}"
            
        finally:
            os.chdir(original_cwd)

def test_idempotency():
    """
    Verifies that running create_directories twice does not raise errors
    and returns 0 on the second run.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # First run
            count_first = create_directories()
            assert count_first > 0, "First run should create directories."
            
            # Second run
            count_second = create_directories()
            assert count_second == 0, "Second run should not create new directories."
            
        finally:
            os.chdir(original_cwd)
