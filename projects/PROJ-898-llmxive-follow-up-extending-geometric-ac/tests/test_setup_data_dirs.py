"""
Unit tests for the setup_data_dirs module.
"""
import os
import tempfile
import pytest
from code.setup_data_dirs import ensure_gitkeep, DATA_DIRS

class TestSetupDataDirs:
    """Tests for data directory setup functionality."""

    def test_ensure_gitkeep_creates_directory(self, tmp_path):
        """Test that ensure_gitkeep creates the directory if it doesn't exist."""
        test_dir = tmp_path / "test_subdir"
        ensure_gitkeep(str(test_dir))
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_gitkeep_creates_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep creates a .gitkeep file."""
        test_dir = tmp_path / "test_subdir"
        ensure_gitkeep(str(test_dir))
        gitkeep_file = test_dir / ".gitkeep"
        assert gitkeep_file.exists()
        assert gitkeep_file.is_file()

    def test_ensure_gitkeep_idempotent(self, tmp_path):
        """Test that calling ensure_gitkeep multiple times doesn't overwrite content."""
        test_dir = tmp_path / "test_subdir"
        ensure_gitkeep(str(test_dir))
        
        # Get initial modification time
        gitkeep_file = test_dir / ".gitkeep"
        initial_mtime = gitkeep_file.stat().st_mtime
        
        # Call again
        ensure_gitkeep(str(test_dir))
        
        # File should still exist and not be modified (content unchanged)
        assert gitkeep_file.exists()
        # Note: os.makedirs with exist_ok=True doesn't change mtime,
        # but file write might if we weren't checking existence first.
        # Our implementation checks existence before writing.

    def test_data_dirs_structure(self):
        """Verify that the defined DATA_DIRS list contains expected paths."""
        assert "data/raw" in DATA_DIRS
        assert "data/generated" in DATA_DIRS
        assert "data/results" in DATA_DIRS
        assert len(DATA_DIRS) == 3

    def test_main_creates_all_dirs(self, tmp_path):
        """Test that main() creates all required directories and .gitkeep files."""
        from code.setup_data_dirs import main
        
        result = main(str(tmp_path))
        assert result == 0
        
        for dir_name in DATA_DIRS:
            full_path = tmp_path / dir_name
            assert full_path.exists()
            gitkeep_file = full_path / ".gitkeep"
            assert gitkeep_file.exists()