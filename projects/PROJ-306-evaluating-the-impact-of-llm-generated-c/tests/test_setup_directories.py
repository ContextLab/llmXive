import os
import tempfile
import shutil
import pytest

# Import the function to test
from code.setup_directories import create_directory

class TestCreateDirectory:
    def test_creates_new_directory(self, tmp_path):
        """Test that a new directory is created successfully."""
        new_dir = tmp_path / "new_subdir"
        assert not new_dir.exists()
        
        result = create_directory(str(new_dir))
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_returns_true_if_exists(self, tmp_path):
        """Test that the function returns True if directory already exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        result = create_directory(str(existing_dir))
        
        assert result is True

    def test_creates_nested_directories(self, tmp_path):
        """Test that nested directories are created when parents don't exist."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()
        
        result = create_directory(str(nested_dir))
        
        assert result is True
        assert nested_dir.exists()
        assert nested_dir.is_dir()
        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()

    def test_handles_invalid_path(self, tmp_path):
        """Test behavior with an invalid path (e.g., file exists where dir expected)."""
        file_path = tmp_path / "a_file.txt"
        file_path.write_text("content")
        
        # Attempting to create a directory where a file exists should fail
        result = create_directory(str(file_path))
        
        assert result is False
