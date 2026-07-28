import pytest
from pathlib import Path
import tempfile
import shutil
import os
import sys

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from create_directories import ensure_directory, PROJECT_DIR, REQUIRED_DIRS

class TestCreateDirectories:
    """Test suite for directory creation functionality."""

    def test_ensure_directory_creates_new_dir(self, tmp_path):
        """Test that ensure_directory creates a new directory."""
        test_dir = tmp_path / "new_test_dir"
        assert not test_dir.exists()
        
        result = ensure_directory(test_dir)
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directory_existing_dir(self, tmp_path):
        """Test that ensure_directory returns True for existing directory."""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        assert test_dir.exists()
        
        result = ensure_directory(test_dir)
        
        assert result is True
        assert test_dir.exists()

    def test_ensure_directory_nested_path(self, tmp_path):
        """Test that ensure_directory creates nested directories."""
        test_dir = tmp_path / "level1" / "level2" / "level3"
        assert not test_dir.exists()
        
        result = ensure_directory(test_dir)
        
        assert result is True
        assert test_dir.exists()
        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()

    def test_required_dirs_list(self):
        """Test that REQUIRED_DIRS contains the expected directory names."""
        expected_dirs = ["data/raw", "data/processed", "code", "tests", "results"]
        assert REQUIRED_DIRS == expected_dirs

    def test_project_dir_structure(self):
        """Test that PROJECT_DIR is constructed correctly."""
        # Check that PROJECT_DIR ends with the expected project name
        assert "PROJ-967-llmxive-follow-up-extending-beyond-scala" in str(PROJECT_DIR)
        
        # Check that it's a Path object
        assert isinstance(PROJECT_DIR, Path)

    def test_directory_creation_integration(self, tmp_path):
        """Integration test: verify all required directories can be created."""
        # Temporarily override PROJECT_DIR for testing
        original_project_dir = PROJECT_DIR
        
        # Create a temporary project structure
        test_project_root = tmp_path / "projects" / "test-project"
        
        # We can't easily override the module-level constant, so we test the logic directly
        for dir_name in REQUIRED_DIRS:
            test_path = test_project_root / dir_name
            result = ensure_directory(test_path)
            assert result is True, f"Failed to create {dir_name}"
            assert test_path.exists()

    def test_directory_permissions(self, tmp_path):
        """Test that created directories have proper permissions."""
        test_dir = tmp_path / "test_permissions"
        ensure_directory(test_dir)
        
        # Check that we can write to the directory
        test_file = test_dir / "test_write.txt"
        try:
            test_file.write_text("test")
            assert test_file.exists()
            test_file.unlink()  # Clean up
        except PermissionError:
            pytest.fail("Created directory does not have write permissions")
