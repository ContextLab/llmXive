"""
Unit tests for data directory structure initialization.
"""
import os
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_data_dirs import setup_data_directories

class TestDataDirectoryStructure:
    """Tests for verifying the data directory structure creation."""

    def test_setup_creates_all_directories(self, tmp_path, monkeypatch):
        """Verify that setup_data_directories creates all required subdirectories."""
        # Monkeypatch the base directory to use a temporary directory
        monkeypatch.chdir(tmp_path)
        
        # Run the setup function
        setup_data_directories()

        # Define expected directories
        expected_dirs = ["raw", "processed", "results", "config", "metadata"]
        
        for subdir in expected_dirs:
            dir_path = tmp_path / "data" / subdir
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_setup_creates_gitkeep_files(self, tmp_path, monkeypatch):
        """Verify that .gitkeep files are created in each directory."""
        monkeypatch.chdir(tmp_path)
        setup_data_directories()

        expected_dirs = ["raw", "processed", "results", "config", "metadata"]
        
        for subdir in expected_dirs:
            gitkeep_path = tmp_path / "data" / subdir / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep file not found in {subdir}"

    def test_setup_idempotent(self, tmp_path, monkeypatch):
        """Verify that running setup multiple times does not cause errors."""
        monkeypatch.chdir(tmp_path)
        
        # Run twice
        setup_data_directories()
        setup_data_directories()

        # Verify directories still exist
        expected_dirs = ["raw", "processed", "results", "config", "metadata"]
        for subdir in expected_dirs:
            dir_path = tmp_path / "data" / subdir
            assert dir_path.exists()