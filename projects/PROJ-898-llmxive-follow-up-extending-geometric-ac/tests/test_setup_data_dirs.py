"""
Unit tests for data directory setup functionality.
"""
import os
import tempfile
import pytest
import shutil
from code.setup_data_dirs import ensure_gitkeep, DATA_DIRS

class TestEnsureGitkeep:
    def test_creates_directory_and_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep creates both directory and .gitkeep file."""
        test_dir = tmp_path / "test_data"
        result = ensure_gitkeep(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()
        assert (test_dir / ".gitkeep").exists()
        assert (test_dir / ".gitkeep").is_file()

    def test_existing_directory_with_gitkeep(self, tmp_path):
        """Test behavior when directory and .gitkeep already exist."""
        test_dir = tmp_path / "existing_data"
        test_dir.mkdir()
        gitkeep = test_dir / ".gitkeep"
        gitkeep.write_text("existing content")
        
        result = ensure_gitkeep(str(test_dir))
        
        assert result is True
        assert gitkeep.read_text() == "existing content"

    def test_existing_directory_without_gitkeep(self, tmp_path):
        """Test that .gitkeep is created in existing directory."""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        
        result = ensure_gitkeep(str(test_dir))
        
        assert result is True
        assert (test_dir / ".gitkeep").exists()

    def test_nested_directory_creation(self, tmp_path):
        """Test creation of nested directory structure."""
        test_dir = tmp_path / "parent" / "child" / "grandchild"
        result = ensure_gitkeep(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        assert (test_dir / ".gitkeep").exists()

class TestDataDirs:
    def test_data_dirs_structure(self):
        """Verify that DATA_DIRS contains the expected paths."""
        assert "data/raw" in DATA_DIRS
        assert "data/generated" in DATA_DIRS
        assert "data/results" in DATA_DIRS
        assert len(DATA_DIRS) == 3

class TestIntegration:
    def test_setup_all_data_dirs(self, tmp_path):
        """Test setting up all data directories in a temporary location."""
        # Change to tmp_path to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Create the directories
            for data_dir in DATA_DIRS:
                full_path = tmp_path / data_dir
                ensure_gitkeep(str(full_path))
            
            # Verify all directories and .gitkeep files exist
            for data_dir in DATA_DIRS:
                full_path = tmp_path / data_dir
                assert full_path.exists()
                assert (full_path / ".gitkeep").exists()
        finally:
            os.chdir(original_cwd)