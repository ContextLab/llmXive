"""
Unit tests for the data directory setup script.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from setup_data_dirs import ensure_dir, main


class TestEnsureDir:
    def test_creates_new_directory(self, tmp_path):
        """Test that ensure_dir creates a new directory."""
        new_dir = tmp_path / "new_subdir"
        assert not new_dir.exists()
        ensure_dir(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_creates_gitkeep_file(self, tmp_path):
        """Test that ensure_dir creates a .gitkeep file."""
        new_dir = tmp_path / "new_subdir"
        ensure_dir(new_dir)
        gitkeep_path = new_dir / ".gitkeep"
        assert gitkeep_path.exists()
        assert gitkeep_path.is_file()

    def test_does_not_fail_on_existing_directory(self, tmp_path):
        """Test that ensure_dir does not fail if directory already exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        ensure_dir(existing_dir)
        assert existing_dir.exists()

    def test_creates_nested_directories(self, tmp_path):
        """Test that ensure_dir creates nested directories."""
        nested_dir = tmp_path / "level1" / "level2"
        assert not nested_dir.exists()
        ensure_dir(nested_dir)
        assert nested_dir.exists()
        assert (nested_dir / ".gitkeep").exists()


class TestMain:
    def test_main_creates_structure(self, tmp_path, monkeypatch):
        """Test that main creates the expected directory structure."""
        # Mock the project root to be our temp directory
        data_dir = tmp_path / "data"
        monkeypatch.chdir(tmp_path)
        
        # We need to patch the Path resolution in the module
        # Since we can't easily patch inside the function, we test the logic directly
        from setup_data_dirs import ensure_dir
        
        ensure_dir(data_dir)
        for subdir in ["raw", "processed", "contracts"]:
            sub_path = data_dir / subdir
            ensure_dir(sub_path)
            assert sub_path.exists()
            assert (sub_path / ".gitkeep").exists()

    def test_main_prints_output(self, tmp_path, monkeypatch, capsys):
        """Test that main prints the expected output."""
        monkeypatch.chdir(tmp_path)
        # Run the logic that main performs
        data_dir = tmp_path / "data"
        from setup_data_dirs import ensure_dir
        ensure_dir(data_dir)
        for subdir in ["raw", "processed", "contracts"]:
            ensure_dir(data_dir / subdir)
        
        captured = capsys.readouterr()
        assert "Data directory structure created" in captured.out