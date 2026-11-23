"""
Tests for T009: Directory creation and verification.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_dirs import ensure_directory, main

class TestDirectoryVerification:
    """Tests for directory creation and verification logic."""

    def test_ensure_directory_creates_missing(self, tmp_path):
        """Test that ensure_directory creates a missing directory."""
        new_dir = tmp_path / "new_subdir"
        assert not new_dir.exists()
        
        result = ensure_directory(new_dir)
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_existing(self, tmp_path):
        """Test that ensure_directory returns True for existing directory."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        result = ensure_directory(existing_dir)
        
        assert result is True
        
    def test_ensure_directory_file_instead_of_dir(self, tmp_path):
        """Test that ensure_directory fails if path is a file."""
        file_path = tmp_path / "not_a_dir"
        file_path.touch()
        
        result = ensure_directory(file_path)
        
        assert result is False
        assert file_path.is_file()

    def test_main_creates_required_dirs(self, tmp_path, monkeypatch):
        """Test that main creates the required directories."""
        # Change CWD to tmp_path to simulate project root
        monkeypatch.chdir(tmp_path)
        
        # Mock the logging to avoid cluttering test output
        import logging
        monkeypatch.setattr(logging, 'info', lambda *args: None)
        monkeypatch.setattr(logging, 'error', lambda *args: None)
        
        # Run main
        exit_code = main()
        
        # Check required directories
        required = ["data/raw", "data/processed", "models", "reports"]
        for rel_path in required:
            full_path = tmp_path / rel_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"
        
        assert exit_code == 0