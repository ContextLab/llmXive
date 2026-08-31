import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_project_structure import create_structure

class TestCreateStructure:
    """Tests for the create_structure function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "code/utils",
            "tests",
            "tests/contract",
            "tests/unit",
            "tests/integration",
            "docs",
            "state"
        ]
        
        created = create_structure(tmp_path)
        
        # Verify the number of directories created
        assert len(created) == len(required_dirs)
        
        # Verify each directory exists
        for dir_name in required_dirs:
            expected_path = tmp_path / dir_name
            assert expected_path.exists(), f"Directory {dir_name} was not created"
            assert expected_path.is_dir(), f"{dir_name} is not a directory"

    def test_creates_parent_directories(self, tmp_path):
        """Verify that parent directories are created when needed."""
        # The function should create 'code/utils' even if 'code' doesn't exist
        created = create_structure(tmp_path)
        
        utils_path = tmp_path / "code" / "utils"
        assert utils_path.exists()
        assert utils_path.is_dir()

    def test_idempotent(self, tmp_path):
        """Verify that running twice doesn't cause errors."""
        # Run twice
        first_run = create_structure(tmp_path)
        second_run = create_structure(tmp_path)
        
        # Should return the same number of directories
        assert len(first_run) == len(second_run)
        
        # All directories should still exist
        for path_str in second_run:
            assert Path(path_str).exists()

    def test_returns_absolute_paths(self, tmp_path):
        """Verify that returned paths are absolute."""
        created = create_structure(tmp_path)
        
        for path_str in created:
            assert Path(path_str).is_absolute()

    def test_handles_existing_directories(self, tmp_path):
        """Verify that existing directories don't cause errors."""
        # Create a directory beforehand
        existing_dir = tmp_path / "docs"
        existing_dir.mkdir()
        
        # Should not raise an exception
        created = create_structure(tmp_path)
        
        # Should still report the directory as created
        assert str(existing_dir) in created