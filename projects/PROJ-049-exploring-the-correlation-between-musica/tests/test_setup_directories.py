"""
Tests for the directory setup functionality.
"""

import os
import tempfile
import shutil
import pytest

# Import the function to test
from setup_directories import create_directory_structure


class TestDirectoryCreation:
    """Test cases for directory creation logic."""

    def setup_method(self):
        """Set up a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up the temporary directory after each test."""
        shutil.rmtree(self.temp_dir)

    def test_creates_all_required_directories(self):
        """Verify all required directories are created."""
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "results",
            "logs",
            "contracts",
        ]
        
        create_directory_structure(self.temp_dir)
        
        for dir_name in required_dirs:
            full_path = os.path.join(self.temp_dir, dir_name)
            assert os.path.isdir(full_path), f"Directory {dir_name} was not created"

    def test_creates_nested_directories(self):
        """Verify nested directories (e.g., data/raw) are created correctly."""
        create_directory_structure(self.temp_dir)
        
        data_raw_path = os.path.join(self.temp_dir, "data", "raw")
        data_processed_path = os.path.join(self.temp_dir, "data", "processed")
        
        assert os.path.isdir(data_raw_path), "Nested directory data/raw not created"
        assert os.path.isdir(data_processed_path), "Nested directory data/processed not created"

    def test_no_error_if_directories_exist(self):
        """Verify the function handles existing directories gracefully."""
        # Pre-create some directories
        os.makedirs(os.path.join(self.temp_dir, "code"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "data", "raw"), exist_ok=True)
        
        # This should not raise an exception
        create_directory_structure(self.temp_dir)
        
        # Verify they still exist
        assert os.path.isdir(os.path.join(self.temp_dir, "code"))
        assert os.path.isdir(os.path.join(self.temp_dir, "data", "raw"))

    def test_creates_in_custom_base_path(self):
        """Verify directories are created relative to the specified base path."""
        custom_base = os.path.join(self.temp_dir, "custom", "subdir")
        
        create_directory_structure(custom_base)
        
        # Check that directories exist relative to the custom base
        code_path = os.path.join(custom_base, "code")
        assert os.path.isdir(code_path), "Directories not created in custom base path"