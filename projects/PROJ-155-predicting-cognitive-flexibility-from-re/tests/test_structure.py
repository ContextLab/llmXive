"""
Unit tests for project structure setup.

Verifies that the required directories exist after running the setup script.
"""
import os
import tempfile
import shutil
import pytest
from code.setup_structure import ensure_dir, get_project_root, create_project_structure


class TestEnsureDir:
    """Tests for the ensure_dir function."""

    def test_create_new_directory(self, tmp_path):
        """Test that a new directory is created."""
        new_dir = tmp_path / "new_test_dir"
        assert not new_dir.exists()
        
        result = ensure_dir(str(new_dir))
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_existing_directory(self, tmp_path):
        """Test that an existing directory returns True."""
        existing_dir = tmp_path / "existing_dir"
        existing_dir.mkdir()
        
        result = ensure_dir(str(existing_dir))
        
        assert result is True
        assert existing_dir.exists()

    def test_nested_directory_creation(self, tmp_path):
        """Test that nested directories are created."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()
        
        result = ensure_dir(str(nested_dir))
        
        assert result is True
        assert nested_dir.exists()


class TestCreateProjectStructure:
    """Tests for the full project structure creation."""

    def test_creates_required_directories(self, tmp_path):
        """Test that all required top-level directories are created."""
        result = create_project_structure(str(tmp_path))
        
        assert result is True
        
        required_dirs = ['code', 'data', 'docs', 'tests']
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_creates_subdirectories(self, tmp_path):
        """Test that essential subdirectories are created."""
        result = create_project_structure(str(tmp_path))
        
        assert result is True
        
        subdirs = [
            'data/raw',
            'data/processed',
            'data/results',
            'code/data',
            'code/utils',
            'code/features',
            'code/analysis'
        ]
        
        for subdir in subdirs:
            dir_path = tmp_path / subdir
            assert dir_path.exists(), f"Subdirectory {subdir} was not created"
            assert dir_path.is_dir(), f"{subdir} is not a directory"


class TestGetProjectRoot:
    """Tests for project root detection."""

    def test_root_detection(self, tmp_path):
        """Test that root detection works correctly."""
        # Change to tmp_path
        original_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            # Create a dummy 'code' dir to simulate project structure
            (tmp_path / 'code').mkdir()
            
            root = get_project_root()
            assert root == str(tmp_path)
        finally:
            os.chdir(original_cwd)