"""
Unit tests for data subdirectory setup (T005).

Tests that the setup_data_subdirs.py script correctly creates:
- data/raw/.gitkeep
- data/processed/.gitkeep
- data/interim/.gitkeep
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.setup_data_subdirs import create_subdirectories, verify_subdirectories


class TestDataSubdirectorySetup:
    """Test cases for data subdirectory setup functionality."""

    def test_create_subdirectories_creates_all_dirs(self):
        """Test that create_subdirectories creates all required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "data"
            base_dir.mkdir()
            
            subdir_names = ["raw", "processed", "interim"]
            
            result = create_subdirectories(base_dir, subdir_names)
            
            assert result is True
            
            for subdir_name in subdir_names:
                subdir_path = base_dir / subdir_name
                assert subdir_path.exists(), f"Directory {subdir_path} was not created"
                assert subdir_path.is_dir(), f"{subdir_path} is not a directory"

    def test_create_subdirectories_creates_gitkeep_files(self):
        """Test that create_subdirectories creates .gitkeep files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "data"
            base_dir.mkdir()
            
            subdir_names = ["raw", "processed", "interim"]
            
            result = create_subdirectories(base_dir, subdir_names)
            
            assert result is True
            
            for subdir_name in subdir_names:
                subdir_path = base_dir / subdir_name
                gitkeep_path = subdir_path / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep file {gitkeep_path} was not created"
                assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"

    def test_verify_subdirectories_returns_true_when_all_exist(self):
        """Test that verify_subdirectories returns True when all directories and files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "data"
            base_dir.mkdir()
            
            subdir_names = ["raw", "processed", "interim"]
            
            # Create the directories and .gitkeep files
            create_subdirectories(base_dir, subdir_names)
            
            result = verify_subdirectories(base_dir, subdir_names)
            
            assert result is True

    def test_verify_subdirectories_returns_false_when_missing(self):
        """Test that verify_subdirectories returns False when directories are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "data"
            base_dir.mkdir()
            
            # Create only one directory
            (base_dir / "raw").mkdir()
            
            subdir_names = ["raw", "processed", "interim"]
            
            result = verify_subdirectories(base_dir, subdir_names)
            
            assert result is False

    def test_verify_subdirectories_returns_false_when_gitkeep_missing(self):
        """Test that verify_subdirectories returns False when .gitkeep files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "data"
            base_dir.mkdir()
            
            # Create directories but not .gitkeep files
            for subdir_name in ["raw", "processed", "interim"]:
                (base_dir / subdir_name).mkdir()
            
            subdir_names = ["raw", "processed", "interim"]
            
            result = verify_subdirectories(base_dir, subdir_names)
            
            assert result is False

    def test_create_subdirectories_idempotent(self):
        """Test that create_subdirectories can be run multiple times without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "data"
            base_dir.mkdir()
            
            subdir_names = ["raw", "processed", "interim"]
            
            # Run twice
            result1 = create_subdirectories(base_dir, subdir_names)
            result2 = create_subdirectories(base_dir, subdir_names)
            
            assert result1 is True
            assert result2 is True
            
            # Verify all still exist
            for subdir_name in subdir_names:
                subdir_path = base_dir / subdir_name
                gitkeep_path = subdir_path / ".gitkeep"
                assert subdir_path.exists()
                assert gitkeep_path.exists()