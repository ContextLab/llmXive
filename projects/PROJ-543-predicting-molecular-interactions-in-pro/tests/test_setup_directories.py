"""
Tests for the setup_directories module.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import setup_directories
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import main

class TestSetupDirectories:
    """Test suite for directory setup functionality."""

    def test_directories_created(self, tmp_path):
        """Test that all required directories are created."""
        # Change to the temporary directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the main function
            result = main()
            
            # Check return code
            assert result == 0, "main() should return 0 on success"
            
            # Verify all directories exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/results",
                "tests",
                "specs"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"
        
        finally:
            os.chdir(original_cwd)

    def test_nested_directories_created(self, tmp_path):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the main function
            main()
            
            # Verify nested structure
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "processed").exists()
            assert (tmp_path / "data" / "results").exists()
            
        finally:
            os.chdir(original_cwd)

    def test_idempotent_execution(self, tmp_path):
        """Test that running the script multiple times doesn't cause errors."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run twice
            result1 = main()
            result2 = main()
            
            assert result1 == 0
            assert result2 == 0
            
        finally:
            os.chdir(original_cwd)