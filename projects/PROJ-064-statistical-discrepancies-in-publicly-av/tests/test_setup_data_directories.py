"""
Tests for the setup_data_directories module.

These tests verify that the directory structure is created correctly
and that .gitkeep files are added to each directory.
"""
import os
import tempfile
import shutil
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_data_directories import setup_data_directories

class TestSetupDataDirectories:
    """Test suite for setup_data_directories function."""
    
    def test_creates_required_directories(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            setup_data_directories(temp_dir)
            
            project_path = Path(temp_dir)
            
            # Check that all required directories exist
            assert (project_path / "data/raw").exists()
            assert (project_path / "data/processed").exists()
            assert (project_path / "state").exists()
            
            # Check that they are directories
            assert (project_path / "data/raw").is_dir()
            assert (project_path / "data/processed").is_dir()
            assert (project_path / "state").is_dir()
    
    def test_creates_gitkeep_files(self):
        """Test that .gitkeep files are created in each directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            setup_data_directories(temp_dir)
            
            project_path = Path(temp_dir)
            
            # Check that .gitkeep files exist
            assert (project_path / "data/raw" / ".gitkeep").exists()
            assert (project_path / "data/processed" / ".gitkeep").exists()
            assert (project_path / "state" / ".gitkeep").exists()
    
    def test_handles_existing_directories(self):
        """Test that the function doesn't fail if directories already exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directories manually first
            project_path = Path(temp_dir)
            (project_path / "data/raw").mkdir(parents=True)
            (project_path / "data/processed").mkdir(parents=True)
            (project_path / "state").mkdir(parents=True)
            
            # Should not raise an exception
            setup_data_directories(temp_dir)
            
            # Directories should still exist
            assert (project_path / "data/raw").exists()
            assert (project_path / "data/processed").exists()
            assert (project_path / "state").exists()
    
    def test_raises_error_for_invalid_project_root(self):
        """Test that an error is raised if project_root doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_dir = os.path.join(temp_dir, "non_existent")
            
            with pytest.raises(ValueError, match="Project root directory does not exist"):
                setup_data_directories(non_existent_dir)
    
    def test_raises_error_if_not_directory(self):
        """Test that an error is raised if project_root is a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file instead of directory
            file_path = os.path.join(temp_dir, "test_file.txt")
            Path(file_path).touch()
            
            with pytest.raises(ValueError, match="Project root is not a directory"):
                setup_data_directories(file_path)
    
    def test_creates_parent_directories(self):
        """Test that parent directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a nested structure where data/ doesn't exist yet
            project_path = Path(temp_dir)
            # Only create the root, not data/
            
            setup_data_directories(temp_dir)
            
            # All directories should be created including parent data/
            assert (project_path / "data").exists()
            assert (project_path / "data/raw").exists()
            assert (project_path / "data/processed").exists()
            assert (project_path / "state").exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])