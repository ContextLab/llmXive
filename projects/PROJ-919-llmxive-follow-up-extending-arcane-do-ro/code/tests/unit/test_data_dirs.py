"""
Unit tests for the data directory setup functionality.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys
import shutil

# Add the code directory to the path to import the setup script
# assuming tests are run from the project root or with proper PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_directories


class TestDataDirectories:
    """Tests for the setup_directories function."""

    def test_directories_created(self, tmp_path):
        """Test that all required directories are created."""
        # Change to the temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the setup
            result = setup_directories()
            
            assert result is True, "setup_directories should return True on success"
            
            # Verify directories exist
            required_dirs = [
                "data/raw",
                "data/derived",
                "data/gold_standard",
                "artifacts"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"
                # Check for .gitkeep file
                gitkeep = dir_path / ".gitkeep"
                assert gitkeep.exists(), f".gitkeep should exist in {dir_name}"
        finally:
            os.chdir(original_cwd)

    def test_directories_idempotent(self, tmp_path):
        """Test that running setup multiple times doesn't fail."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run setup twice
            result1 = setup_directories()
            result2 = setup_directories()
            
            assert result1 is True
            assert result2 is True
            
            # Verify directories still exist and are valid
            required_dirs = [
                "data/raw",
                "data/derived",
                "data/gold_standard",
                "artifacts"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists()
                assert dir_path.is_dir()
        finally:
            os.chdir(original_cwd)

    def test_parent_directories_created(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Ensure 'data' doesn't exist initially
            data_dir = tmp_path / "data"
            assert not data_dir.exists()
            
            result = setup_directories()
            
            assert result is True
            assert data_dir.exists()
            assert data_dir.is_dir()
        finally:
            os.chdir(original_cwd)