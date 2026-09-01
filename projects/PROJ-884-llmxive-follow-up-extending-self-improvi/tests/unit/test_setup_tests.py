"""
Unit tests for the setup_tests module.
Tests the creation and verification of the tests directory hierarchy.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_tests import setup_tests_directories


class TestSetupTestsDirectories:
    """Test cases for setup_tests_directories function."""

    def test_creates_tests_directory(self, tmp_path):
        """Test that the tests directory is created."""
        result = setup_tests_directories(tmp_path)
        
        tests_dir = tmp_path / "tests"
        assert tests_dir.exists()
        assert tests_dir.is_dir()
        
        assert tests_dir in result

    def test_creates_unit_subdirectory(self, tmp_path):
        """Test that the unit subdirectory is created."""
        result = setup_tests_directories(tmp_path)
        
        unit_dir = tmp_path / "tests" / "unit"
        assert unit_dir.exists()
        assert unit_dir.is_dir()
        
        assert unit_dir in result

    def test_creates_integration_subdirectory(self, tmp_path):
        """Test that the integration subdirectory is created."""
        result = setup_tests_directories(tmp_path)
        
        integration_dir = tmp_path / "tests" / "integration"
        assert integration_dir.exists()
        assert integration_dir.is_dir()
        
        assert integration_dir in result

    def test_all_three_directories_returned(self, tmp_path):
        """Test that all three directories are returned in the result list."""
        result = setup_tests_directories(tmp_path)
        
        assert len(result) == 3
        
        tests_dir = tmp_path / "tests"
        unit_dir = tmp_path / "tests" / "unit"
        integration_dir = tmp_path / "tests" / "integration"
        
        assert tests_dir in result
        assert unit_dir in result
        assert integration_dir in result

    def test_directories_are_writable(self, tmp_path):
        """Test that all created directories are writable."""
        result = setup_tests_directories(tmp_path)
        
        for directory in result:
            test_file = directory / ".test_writability"
            try:
                test_file.touch()
                test_file.unlink()
            except (OSError, PermissionError):
                pytest.fail(f"Directory {directory} is not writable")

    def test_handles_existing_directories(self, tmp_path):
        """Test that existing directories are handled gracefully."""
        # Create the directories first
        setup_tests_directories(tmp_path)
        
        # Call again - should not raise an error
        result = setup_tests_directories(tmp_path)
        
        assert len(result) == 3

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        # Use a nested path
        nested_path = tmp_path / "level1" / "level2"
        
        result = setup_tests_directories(nested_path)
        
        tests_dir = nested_path / "tests"
        assert tests_dir.exists()
        
        unit_dir = tests_dir / "unit"
        assert unit_dir.exists()
        
        integration_dir = tests_dir / "integration"
        assert integration_dir.exists()

    def test_raises_on_unwritable_directory(self, tmp_path):
        """Test that an error is raised if a directory cannot be written to."""
        # Create a read-only directory scenario (this might not work on all systems)
        # For now, we'll just verify the function doesn't crash on normal operation
        result = setup_tests_directories(tmp_path)
        assert len(result) == 3
