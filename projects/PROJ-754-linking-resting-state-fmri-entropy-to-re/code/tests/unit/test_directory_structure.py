import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import the script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from create_project_structure import ensure_directory, get_project_root

class TestDirectoryStructure:
    """Test that the directory creation logic works correctly for T002."""

    def test_ensure_directory_creates_new(self, tmp_path):
        """Test that ensure_directory creates a new directory if it doesn't exist."""
        new_dir = tmp_path / "new" / "sub" / "directory"
        assert not new_dir.exists()
        
        result = ensure_directory(new_dir)
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_existing(self, tmp_path):
        """Test that ensure_directory returns True if directory already exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir(parents=True)
        
        result = ensure_directory(existing_dir)
        
        assert result is True
        assert existing_dir.exists()

    def test_required_source_subdirs(self, tmp_path):
        """Test that all required source subdirectories are created."""
        required_dirs = [
            "data",
            "analysis",
            "stats",
            "config",
            "utils",
            "entities"
        ]
        
        for subdir in required_dirs:
            dir_path = tmp_path / subdir
            ensure_directory(dir_path)
            assert dir_path.exists()
            assert dir_path.is_dir()

    def test_required_test_subdirs(self, tmp_path):
        """Test that all required test subdirectories are created."""
        required_dirs = [
            "unit",
            "integration"
        ]
        
        for subdir in required_dirs:
            dir_path = tmp_path / subdir
            ensure_directory(dir_path)
            assert dir_path.exists()
            assert dir_path.is_dir()

    def test_full_structure_creation(self, tmp_path):
        """Test creation of the full directory structure for T002."""
        # Simulate the structure creation for a project root
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Create source subdirectories
        src_dirs = [
            "data", "analysis", "stats", "config", "utils", "entities"
        ]
        for subdir in src_dirs:
            ensure_directory(project_root / "src" / subdir)
        
        # Create test subdirectories
        test_dirs = ["unit", "integration"]
        for subdir in test_dirs:
            ensure_directory(project_root / "tests" / subdir)
        
        # Verify all directories exist
        for subdir in src_dirs:
            assert (project_root / "src" / subdir).exists()
        
        for subdir in test_dirs:
            assert (project_root / "tests" / subdir).exists()
