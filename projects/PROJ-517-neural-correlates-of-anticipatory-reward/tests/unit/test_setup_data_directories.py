"""
Unit tests for T001c: setup_data_directories.py
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We will test the logic by mocking the paths or running in a temp directory
# Since the script uses global paths, we test the function logic directly if possible
# or by patching the base path.

from setup_data_directories import create_directory

class TestDataDirectories:
    """Tests for the data directory creation logic."""

    def test_create_new_directory(self, tmp_path):
        """Test that a new directory is created successfully."""
        test_dir = tmp_path / "new_test_dir"
        assert not test_dir.exists()
        
        # Change to tmp_path context for relative path testing
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # We need to test with relative path logic
            # The function takes a string path, which is interpreted relative to cwd
            result = create_directory("new_test_dir")
            
            assert result is True
            assert test_dir.exists()
            assert test_dir.is_dir()
        finally:
            os.chdir(original_cwd)

    def test_create_existing_directory(self, tmp_path):
        """Test that an existing directory returns True without error."""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = create_directory("existing_dir")
            
            assert result is True
            assert test_dir.exists()
        finally:
            os.chdir(original_cwd)

    def test_create_nested_directory(self, tmp_path):
        """Test that nested directories are created with parents=True."""
        nested_path = tmp_path / "level1" / "level2" / "level3"
        assert not nested_path.exists()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = create_directory("level1/level2/level3")
            
            assert result is True
            assert nested_path.exists()
            assert nested_path.is_dir()
        finally:
            os.chdir(original_cwd)

    def test_create_directory_permissions(self, tmp_path):
        """Test directory creation and basic permissions check."""
        test_dir = tmp_path / "perm_test"
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = create_directory("perm_test")
            
            assert result is True
            # Check if we can list the directory (implies read/execute perms)
            list(test_dir.iterdir())
        finally:
            os.chdir(original_cwd)