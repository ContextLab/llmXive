"""
Unit tests for the setup_data_raw.py script.
Verifies that the data/raw directory is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_raw import main
from setup_directories import create_directory


def test_setup_data_raw_creates_directory():
    """Test that setup_data_raw creates the data/raw directory."""
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create the parent data directory first
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            # Run the setup function
            result = main()
            
            # Verify the directory was created
            raw_dir = Path("data/raw")
            assert raw_dir.exists(), f"Directory {raw_dir} was not created"
            assert raw_dir.is_dir(), f"{raw_dir} exists but is not a directory"
            
            # Verify return code
            assert result == 0, f"main() returned {result}, expected 0"
            
        finally:
            os.chdir(original_cwd)


def test_setup_data_raw_idempotent():
    """Test that running setup_data_raw multiple times doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create the parent data directory
            Path("data").mkdir(exist_ok=True)
            
            # Run twice
            result1 = main()
            result2 = main()
            
            # Both should succeed
            assert result1 == 0
            assert result2 == 0
            
            # Directory should still exist
            assert Path("data/raw").exists()
            
        finally:
            os.chdir(original_cwd)