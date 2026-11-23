import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_gitkeep import create_gitkeep_in_directory, initialize_data_directories

class TestCreateGitkeep:
    def test_creates_gitkeep_in_existing_directory(self, tmp_path):
        """Test that .gitkeep is created in an existing directory."""
        result = create_gitkeep_in_directory(tmp_path)
        assert result is True
        assert (tmp_path / ".gitkeep").exists()

    def test_returns_true_if_gitkeep_already_exists(self, tmp_path):
        """Test that function returns True if .gitkeep already exists."""
        # Create .gitkeep first
        (tmp_path / ".gitkeep").touch()
        
        result = create_gitkeep_in_directory(tmp_path)
        assert result is True

    def test_returns_false_for_nonexistent_directory(self):
        """Test that function returns False for non-existent directory."""
        non_existent = Path("/non/existent/path/12345")
        result = create_gitkeep_in_directory(non_existent)
        assert result is False

class TestInitializeDataDirectories:
    def test_creates_all_required_subdirectories(self, tmp_path, monkeypatch):
        """Test that all required data subdirectories are created with .gitkeep."""
        # Monkeypatch the project root
        monkeypatch.chdir(tmp_path)
        
        result = initialize_data_directories()
        assert result is True
        
        # Verify all directories exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "results").exists()
        
        # Verify .gitkeep files exist in each
        assert (tmp_path / "data" / ".gitkeep").exists()
        assert (tmp_path / "data" / "raw" / ".gitkeep").exists()
        assert (tmp_path / "data" / "processed" / ".gitkeep").exists()
        assert (tmp_path / "data" / "results" / ".gitkeep").exists()

    def test_handles_existing_directories_gracefully(self, tmp_path, monkeypatch):
        """Test that function handles pre-existing directories correctly."""
        monkeypatch.chdir(tmp_path)
        
        # Pre-create some directories
        (tmp_path / "data" / "raw").mkdir(parents=True)
        
        # First run
        result1 = initialize_data_directories()
        assert result1 is True
        
        # Second run (should still succeed)
        result2 = initialize_data_directories()
        assert result2 is True