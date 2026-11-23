"""
Unit tests for the directory setup functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the parent directory to the path so we can import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directories


class TestDirectoryCreation:
    """Test cases for directory creation functionality."""

    def setup_method(self):
        """Set up a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up the temporary directory after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_core_directories_created(self):
        """Test that all core directories are created."""
        created_dirs = create_directories()
        
        # Check that core directories exist
        core_dirs = ["code", "data", "tests", "docs"]
        for dir_name in core_dirs:
            path = Path(self.temp_dir) / dir_name
            assert path.exists(), f"Core directory {dir_name} was not created"
            assert path.is_dir(), f"{dir_name} is not a directory"

    def test_code_subdirectories_created(self):
        """Test that code subdirectories are created."""
        create_directories()
        
        code_subdirs = [
            "code/data_acquisition",
            "code/feature_extraction",
            "code/analysis",
            "code/utils"
        ]
        
        for subdir in code_subdirs:
            path = Path(self.temp_dir) / subdir
            assert path.exists(), f"Code subdirectory {subdir} was not created"
            assert path.is_dir(), f"{subdir} is not a directory"

    def test_data_subdirectories_created(self):
        """Test that data subdirectories are created."""
        create_directories()
        
        data_subdirs = [
            "data/raw",
            "data/processed"
        ]
        
        for subdir in data_subdirs:
            path = Path(self.temp_dir) / subdir
            assert path.exists(), f"Data subdirectory {subdir} was not created"
            assert path.is_dir(), f"{subdir} is not a directory"

    def test_directories_already_exist(self):
        """Test that the function handles existing directories gracefully."""
        # Create directories first
        create_directories()
        
        # Run again - should not raise errors
        created_dirs = create_directories()
        
        # Should report that directories already exist
        # (the function should handle this gracefully)
        assert len(created_dirs) == 0  # No new directories created

    def test_nested_directory_creation(self):
        """Test that nested directories are created correctly."""
        # Remove intermediate directories to test parent creation
        create_directories()
        
        # Verify the full hierarchy
        expected_paths = [
            "code/data_acquisition",
            "code/feature_extraction",
            "code/analysis",
            "code/utils",
            "data/raw",
            "data/processed"
        ]
        
        for path_str in expected_paths:
            path = Path(self.temp_dir) / path_str
            assert path.exists(), f"Nested path {path_str} was not created"
            assert path.is_dir(), f"{path_str} is not a directory"
            # Also verify parent directories exist
            parent = path.parent
            while parent != Path(self.temp_dir):
                assert parent.exists(), f"Parent directory {parent} missing"
                parent = parent.parent
