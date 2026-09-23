"""
Unit tests for the project setup script (T001a).

Verifies that the directory structure is created correctly.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import main


class TestProjectStructure:
    """Tests for project directory creation."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        # Change to the temporary directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the main function
            result = main()
            
            # Check return code
            assert result == 0, "Setup script should return 0 on success"
            
            # Verify specific directories exist
            required_dirs = [
                "code",
                "code/utils",
                "tests",
                "data/raw",
                "data/processed",
                "data/synthetic",
                "models",
                "docs",
                "docs/contracts",
                "state/projects",
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
                
        finally:
            os.chdir(original_cwd)

    def test_handles_existing_directories(self, tmp_path):
        """Verify that the script handles pre-existing directories gracefully."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Pre-create one directory
            (tmp_path / "code").mkdir()
            
            # Run the main function
            result = main()
            
            # Should still succeed
            assert result == 0
            
            # Verify the pre-existing directory is still there
            assert (tmp_path / "code").exists()
            
        finally:
            os.chdir(original_cwd)

    def test_nested_structure_created(self, tmp_path):
        """Verify that nested directories (e.g., code/utils) are created."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            result = main()
            assert result == 0
            
            # Check nested structure
            assert (tmp_path / "code" / "utils").exists()
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "docs" / "contracts").exists()
            assert (tmp_path / "state" / "projects").exists()
            
        finally:
            os.chdir(original_cwd)