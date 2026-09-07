"""
Tests for gitkeep initialization functionality.

These tests verify that .gitkeep files are correctly created in data directories.
"""
import os
import tempfile
from pathlib import Path
import pytest

from setup_gitkeep import create_gitkeep_in_directory, initialize_data_directories


class TestGitkeepCreation:
    """Test cases for .gitkeep file creation."""
    
    def test_create_gitkeep_new_file(self, tmp_path: Path):
        """Test creating a .gitkeep file in a directory that doesn't have one."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        gitkeep_path = test_dir / ".gitkeep"
        assert not gitkeep_path.exists()
        
        create_gitkeep_in_directory(test_dir)
        
        assert gitkeep_path.exists()
        assert gitkeep_path.is_file()
        
        # Verify file content
        with open(gitkeep_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "git" in content.lower()
    
    def test_create_gitkeep_existing_file(self, tmp_path: Path):
        """Test that .gitkeep is not overwritten if it already exists."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        gitkeep_path = test_dir / ".gitkeep"
        gitkeep_path.write_text("existing content")
        
        create_gitkeep_in_directory(test_dir)
        
        # File should still exist with original content
        assert gitkeep_path.exists()
        with open(gitkeep_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == "existing content"
    
    def test_create_gitkeep_creates_directory(self, tmp_path: Path):
        """Test that .gitkeep creation also creates the directory if needed."""
        test_dir = tmp_path / "nonexistent" / "test_dir"
        
        # Directory should not exist yet
        assert not test_dir.exists()
        
        create_gitkeep_in_directory(test_dir)
        
        # Directory and file should now exist
        assert test_dir.exists()
        assert (test_dir / ".gitkeep").exists()


class TestDataDirectoryInitialization:
    """Test cases for initializing data directories."""
    
    def test_initializes_all_required_subdirectories(self, tmp_path: Path):
        """Test that all required data subdirectories are initialized."""
        data_dir = tmp_path / "data"
        
        initialize_data_directories(tmp_path)
        
        # Check that all required subdirectories exist
        required_subdirs = ["raw", "processed", "results"]
        for subdir_name in required_subdirs:
            subdir_path = data_dir / subdir_name
            assert subdir_path.exists(), f"Subdirectory {subdir_name} was not created"
            assert (subdir_path / ".gitkeep").exists(), f".gitkeep missing in {subdir_name}"
    
    def test_creates_base_data_directory(self, tmp_path: Path):
        """Test that the base data directory is created if it doesn't exist."""
        data_dir = tmp_path / "data"
        assert not data_dir.exists()
        
        initialize_data_directories(tmp_path)
        
        assert data_dir.exists()
        assert data_dir.is_dir()
    
    def test_handles_existing_data_structure(self, tmp_path: Path):
        """Test that existing data structure is handled correctly."""
        # Create existing data structure
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "raw").mkdir()
        (data_dir / "raw" / ".gitkeep").write_text("existing")
        
        # Should not fail or overwrite existing .gitkeep
        initialize_data_directories(tmp_path)
        
        # Verify existing .gitkeep was preserved
        with open(data_dir / "raw" / ".gitkeep", "r", encoding="utf-8") as f:
            content = f.read()
        assert content == "existing"
    
    def test_creates_missing_subdirectories(self, tmp_path: Path):
        """Test that missing subdirectories are created."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        # Only create 'raw', missing 'processed' and 'results'
        (data_dir / "raw").mkdir()
        
        initialize_data_directories(tmp_path)
        
        # All subdirectories should now exist
        assert (data_dir / "processed").exists()
        assert (data_dir / "results").exists()
        assert (data_dir / "processed" / ".gitkeep").exists()
        assert (data_dir / "results" / ".gitkeep").exists()