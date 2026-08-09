"""
Unit tests for verifying the project structure initialization.

These tests ensure that the required directories exist after running
the setup script or manually creating them.
"""
import os
import tempfile
import pytest
import shutil

# Import the function to test
from code.setup_structure import BASE_DIRS, create_directories

class TestProjectStructure:
    """Tests for project directory creation."""

    def test_base_dirs_defined(self):
        """Verify that the list of base directories is populated."""
        assert len(BASE_DIRS) > 0
        assert "code" in BASE_DIRS
        assert "data/raw" in BASE_DIRS
        assert "data/derived" in BASE_DIRS
        assert "data/results" in BASE_DIRS
        assert "specs" in BASE_DIRS
        assert "tests" in BASE_DIRS

    def test_create_directories_function(self, tmp_path):
        """Test that create_directories creates the expected folders."""
        # tmp_path is a pytest fixture providing a temporary directory
        create_directories(str(tmp_path))
        
        for dir_name in BASE_DIRS:
            expected_path = tmp_path / dir_name
            assert expected_path.exists(), f"Directory {dir_name} was not created"
            assert expected_path.is_dir(), f"{dir_name} is not a directory"

    def test_create_directories_idempotent(self, tmp_path):
        """Test that running create_directories twice doesn't raise errors."""
        create_directories(str(tmp_path))
        # Run again
        create_directories(str(tmp_path))
        
        for dir_name in BASE_DIRS:
            expected_path = tmp_path / dir_name
            assert expected_path.exists()

    def test_nested_structure_created(self, tmp_path):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        create_directories(str(tmp_path))
        
        # Check nested paths specifically
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "derived").exists()
        assert (tmp_path / "data" / "results").exists()
        
        # Ensure 'data' itself is a directory
        assert (tmp_path / "data").is_dir()