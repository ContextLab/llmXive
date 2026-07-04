"""
Tests for T001: Project structure creation.

Verifies that the setup script creates the required directories.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys
import pytest

# Add the code directory to the path so we can import the setup script
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_structure import main as setup_main

class TestProjectStructure:
    """Test cases for project structure creation."""

    def test_creates_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        # Change to the temporary directory
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup script
            result = setup_main()
            
            # Verify exit code
            assert result == 0, "Setup script should return 0 on success"
            
            # Define required directories
            required_dirs = [
                "code",
                "tests",
                "data/raw",
                "data/logs",
                "data/analysis",
                "figures",
                "contracts",
                "specs"
            ]
            
            # Verify each directory exists
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_handles_existing_directories(self, tmp_path):
        """Verify that the script handles existing directories gracefully."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            # Pre-create one directory
            (tmp_path / "code").mkdir()
            
            # Run the setup script
            result = setup_main()
            
            # Verify exit code
            assert result == 0, "Setup script should return 0 even with existing dirs"
            
            # Verify the directory still exists
            assert (tmp_path / "code").exists()
        finally:
            os.chdir(original_cwd)
