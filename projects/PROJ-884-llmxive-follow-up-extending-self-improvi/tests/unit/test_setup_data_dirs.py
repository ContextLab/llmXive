"""
Unit tests for the setup_data_dirs module.
Tests directory creation and writability verification.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories

class TestSetupDataDirectories:
    """Test cases for setup_data_directories function."""

    def test_creates_directory_structure(self, tmp_path):
        """Test that the function creates the required directory hierarchy."""
        directories = setup_data_directories(tmp_path)
        
        # Check that we got 3 directories
        assert len(directories) == 3
        
        # Check directory names
        dir_names = [d.name for d in directories]
        assert "data" in dir_names
        assert "raw" in dir_names
        assert "processed" in dir_names
        
        # Check that directories actually exist
        for dir_path in directories:
            assert dir_path.exists()
            assert dir_path.is_dir()

    def test_creates_nested_structure(self, tmp_path):
        """Test that nested directories are created correctly."""
        directories = setup_data_directories(tmp_path)
        
        # Find the raw and processed directories
        raw_dir = next(d for d in directories if d.name == "raw")
        processed_dir = next(d for d in directories if d.name == "processed")
        
        # Verify they are subdirectories of data
        assert raw_dir.parent.name == "data"
        assert processed_dir.parent.name == "data"

    def test_verifies_writability(self, tmp_path):
        """Test that the function verifies writability of directories."""
        # This should not raise an exception if directories are writable
        directories = setup_data_directories(tmp_path)
        
        # Verify we can write a test file
        test_file = directories[1] / "test_write.txt"  # raw directory
        test_file.write_text("test content")
        assert test_file.exists()
        test_file.unlink()

    def test_handles_existing_directories(self, tmp_path):
        """Test that the function handles existing directories gracefully."""
        # Create the directories first
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        
        data_dir.mkdir()
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Should not raise an exception
        directories = setup_data_directories(tmp_path)
        
        assert len(directories) == 3
        assert all(d.exists() for d in directories)

    def test_raises_on_unwritable_directory(self, tmp_path):
        """Test that the function raises an error for unwritable directories."""
        # Create a read-only directory structure
        data_dir = tmp_path / "data"
        data_dir.mkdir(mode=0o555)  # Read and execute only
        
        try:
            # This should raise a RuntimeError
            with pytest.raises(RuntimeError) as exc_info:
                setup_data_directories(tmp_path)
            
            assert "not writable" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            data_dir.chmod(0o755)

    def test_returns_correct_paths(self, tmp_path):
        """Test that the function returns the correct Path objects."""
        directories = setup_data_directories(tmp_path)
        
        data_dir = directories[0]
        raw_dir = directories[1]
        processed_dir = directories[2]
        
        assert data_dir == tmp_path / "data"
        assert raw_dir == tmp_path / "data" / "raw"
        assert processed_dir == tmp_path / "data" / "processed"
        
        # Verify they are Path objects
        assert isinstance(data_dir, Path)
        assert isinstance(raw_dir, Path)
        assert isinstance(processed_dir, Path)
