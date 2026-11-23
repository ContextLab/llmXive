"""
Unit tests for the setup_directories module.
Tests the creation and verification logic of the directory setup script.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the functions to test
# We need to ensure the import path works relative to the project structure
# Since this is a unit test, we might mock or adjust sys.path if running in isolation
# However, per project structure, we assume code/ is importable or we test logic directly

# To avoid import issues in a pure unit test context without full project setup,
# we will test the logic by importing the specific functions if possible, 
# or by testing the expected behavior of the paths.

# Assuming the script is at code/setup_directories.py
# We can import the module if we add the parent of 'code' to sys.path
# But since 'code' is a package here, let's import the specific logic if we can
# For now, we will test the expected behavior of the directory creation logic.

# Mocking the functions for isolation if needed, or testing the logic directly.
# Let's assume we can import the functions by adding the project root to path.

import sys
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup_directories import create_directory, verify_directory, REQUIRED_ROOT_DIRS

class TestCreateDirectory:
    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory that doesn't exist."""
        new_dir = tmp_path / "new_test_dir"
        assert not new_dir.exists()
        
        result = create_directory(new_dir)
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_existing_directory(self, tmp_path):
        """Test creating a directory that already exists."""
        existing_dir = tmp_path / "existing_dir"
        existing_dir.mkdir()
        
        result = create_directory(existing_dir)
        
        assert result is True
        assert existing_dir.exists()

    def test_create_nested_directory(self, tmp_path):
        """Test creating nested directories."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()
        
        result = create_directory(nested_dir)
        
        assert result is True
        assert nested_dir.exists()

class TestVerifyDirectory:
    def test_verify_existing_directory(self, tmp_path):
        """Test verifying an existing directory."""
        existing_dir = tmp_path / "existing_dir"
        existing_dir.mkdir()
        
        result = verify_directory(existing_dir)
        
        assert result is True

    def test_verify_nonexistent_directory_raises(self, tmp_path):
        """Test that verifying a non-existent directory raises FileNotFoundError."""
        non_existent_dir = tmp_path / "non_existent_dir"
        
        with pytest.raises(FileNotFoundError):
            verify_directory(non_existent_dir)

class TestRequiredRootDirs:
    def test_required_dirs_list(self):
        """Test that REQUIRED_ROOT_DIRS contains the expected directories."""
        assert "code" in REQUIRED_ROOT_DIRS
        assert "tests" in REQUIRED_ROOT_DIRS
        assert "data" in REQUIRED_ROOT_DIRS
        assert len(REQUIRED_ROOT_DIRS) == 3