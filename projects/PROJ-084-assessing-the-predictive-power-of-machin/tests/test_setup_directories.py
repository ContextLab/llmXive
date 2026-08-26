"""
Tests for the setup_directories module.

These tests verify that the directory creation logic works correctly.
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We need to add the code directory to the path to import setup_directories
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import main


class TestSetupDirectories:
    """Test cases for directory setup."""

    def test_creates_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        # Change to tmp directory to avoid modifying actual project structure
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup
            main()
            
            # Check that all required directories exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/results",
                "tests",
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
        finally:
            os.chdir(original_cwd)

    def test_creates_gitkeep_files(self, tmp_path):
        """Test that .gitkeep files are created in data directories."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            main()
            
            data_dirs = ["data/raw", "data/processed", "data/results"]
            for data_dir in data_dirs:
                gitkeep_path = tmp_path / data_dir / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep not found in {data_dir}"
                assert gitkeep_path.is_file(), f"{data_dir}/.gitkeep is not a file"
        finally:
            os.chdir(original_cwd)

    def test_idempotent_execution(self, tmp_path):
        """Test that running the script twice doesn't cause errors."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            # Run twice
            main()
            main()
            
            # Should still have all directories
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/results",
                "tests",
            ]
            
            for dir_name in required_dirs:
                assert (tmp_path / dir_name).exists()
        finally:
            os.chdir(original_cwd)