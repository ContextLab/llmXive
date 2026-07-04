"""
Unit tests for the create_directories script.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from create_directories import main

def test_directory_creation():
    """Test that all required directories are created."""
    # Create a temporary directory to act as the root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the main function
            main()
            
            # Verify directories exist
            required_dirs = [
                "code",
                "data",
                "tests",
                "data/raw",
                "data/processed",
                "data/metadata",
                "tests/unit",
                "tests/integration",
            ]
            
            for dir_name in required_dirs:
                full_path = Path(tmp_dir) / dir_name
                assert full_path.exists(), f"Directory {dir_name} was not created"
                assert full_path.is_dir(), f"Path {dir_name} exists but is not a directory"
                
        finally:
            os.chdir(original_cwd)

def test_idempotency():
    """Test that running the script twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run main twice
            main()
            main()
            
            # Verify all directories still exist
            required_dirs = [
                "code", "data", "tests",
                "data/raw", "data/processed", "data/metadata",
                "tests/unit", "tests/integration"
            ]
            
            for dir_name in required_dirs:
                full_path = Path(tmp_dir) / dir_name
                assert full_path.exists() and full_path.is_dir()
                
        finally:
            os.chdir(original_cwd)