"""
Tests for the directory setup script (Task T001a).

Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the main function from the setup script
# We assume the script is in code/setup_directories.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import main as setup_main

def test_directory_structure_creation():
    """Test that all required directories are created."""
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the setup script
            setup_main()
            
            # Verify directories exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "results",
                "specs"
            ]
            
            for dir_name in required_dirs:
                dir_path = Path(tmp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
                
                # Check nested structure for data
                if dir_name == "data":
                    assert (Path(tmp_dir) / "data/raw").exists(), "data/raw was not created"
                    assert (Path(tmp_dir) / "data/processed").exists(), "data/processed was not created"
                    
        finally:
            os.chdir(original_cwd)

def test_idempotency():
    """Test that running the script twice does not cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run setup first time
            setup_main()
            
            # Run setup second time (should skip existing dirs)
            setup_main()
            
            # Verify all still exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "results",
                "specs"
            ]
            
            for dir_name in required_dirs:
                dir_path = Path(tmp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_name} missing after second run"
                    
        finally:
            os.chdir(original_cwd)