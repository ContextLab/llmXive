"""
Tests for directory initialization functionality.

This module contains tests to verify that the setup_directories.py script
correctly creates the required project directory structure.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directories, verify_structure, REQUIRED_DIRS


class TestDirectoryInitialization:
    """Test cases for directory initialization functions."""

    def test_create_directories_creates_all_required_dirs(self):
        """Test that create_directories creates all required directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            # Create directories
            result = create_directories(base_path)
            
            # Verify result is True
            assert result is True, "create_directories should return True on success"
            
            # Verify all required directories exist
            for dir_name in REQUIRED_DIRS:
                dir_path = base_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"

    def test_create_directories_handles_existing_dirs(self):
        """Test that create_directories handles already existing directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            # Create some directories manually first
            (base_path / "code").mkdir()
            (base_path / "data").mkdir()
            
            # Create directories again
            result = create_directories(base_path)
            
            # Should still succeed
            assert result is True
            
            # Verify all directories still exist
            for dir_name in REQUIRED_DIRS:
                dir_path = base_path / dir_name
                assert dir_path.exists()

    def test_verify_structure_returns_true_for_complete_structure(self):
        """Test that verify_structure returns True when all dirs exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            # Create complete structure
            create_directories(base_path)
            
            # Verify structure
            result = verify_structure(base_path)
            
            assert result is True, "verify_structure should return True for complete structure"

    def test_verify_structure_returns_false_for_incomplete_structure(self):
        """Test that verify_structure returns False when some dirs missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            # Create only some directories
            (base_path / "code").mkdir()
            (base_path / "tests").mkdir()
            
            # Verify structure (should fail)
            result = verify_structure(base_path)
            
            assert result is False, "verify_structure should return False for incomplete structure"

    def test_required_dirs_list_is_not_empty(self):
        """Test that REQUIRED_DIRS list contains expected directories."""
        assert len(REQUIRED_DIRS) > 0, "REQUIRED_DIRS should not be empty"
        assert "code" in REQUIRED_DIRS, "REQUIRED_DIRS should include 'code'"
        assert "tests" in REQUIRED_DIRS, "REQUIRED_DIRS should include 'tests'"
        assert "data" in REQUIRED_DIRS, "REQUIRED_DIRS should include 'data'"
        assert "docs" in REQUIRED_DIRS, "REQUIRED_DIRS should include 'docs'"

    def test_directory_creation_preserves_parent_structure(self):
        """Test that nested directories are created with parents."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            # Create directories
            create_directories(base_path)
            
            # Verify nested directories exist
            nested_dirs = [
                "data/raw",
                "code/utils",
                "tests/unit"
            ]
            
            for dir_name in nested_dirs:
                dir_path = base_path / dir_name
                assert dir_path.exists(), f"Nested directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])