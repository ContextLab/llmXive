"""
Tests for the setup_directories script.
Verifies that the required directories are created correctly.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from setup_directories import main

def test_directory_creation():
    """Test that main() creates the required directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the setup script
            main()
            
            # Verify directories exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/results",
                "tests"
            ]
            
            for dir_name in required_dirs:
                dir_path = Path(tmp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"
        
        finally:
            os.chdir(original_cwd)