import os
import pytest
from pathlib import Path
from code.setup_data_dirs import create_data_directories, verify_data_directories

class TestDataDirectories:
    """Unit tests for data directory creation and verification."""

    def test_create_data_directories_creates_structure(self, tmp_path, monkeypatch):
        """Test that create_data_directories creates the expected structure."""
        # Change to temp directory for testing
        monkeypatch.chdir(tmp_path)
        
        # Create the directories
        create_data_directories()
        
        # Verify directories exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "models").exists()
        
        # Verify .gitkeep files exist
        assert (tmp_path / "data" / "raw" / ".gitkeep").exists()
        assert (tmp_path / "data" / "processed" / ".gitkeep").exists()
        assert (tmp_path / "data" / "models" / ".gitkeep").exists()

    def test_verify_data_directories_returns_true_when_exist(self, tmp_path, monkeypatch):
        """Test that verify_data_directories returns True when directories exist."""
        monkeypatch.chdir(tmp_path)
        
        # Create directories first
        create_data_directories()
        
        # Verify returns True
        assert verify_data_directories() is True

    def test_verify_data_directories_returns_false_when_missing(self, tmp_path, monkeypatch):
        """Test that verify_data_directories returns False when directories are missing."""
        monkeypatch.chdir(tmp_path)
        
        # Don't create directories, just verify
        assert verify_data_directories() is False

    def test_create_data_directories_idempotent(self, tmp_path, monkeypatch):
        """Test that creating directories multiple times doesn't cause errors."""
        monkeypatch.chdir(tmp_path)
        
        # Create directories twice
        create_data_directories()
        create_data_directories()
        
        # Verify they still exist
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "models").exists()
