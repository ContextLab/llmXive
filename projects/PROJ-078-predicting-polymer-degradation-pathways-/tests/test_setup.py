"""
Tests for project setup and directory structure verification.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import create_directories, verify_directories


class TestSetupProject:
    """Test cases for setup_project module."""

    def test_create_directories_creates_all_required(self, tmp_path):
        """Test that create_directories creates all required directories."""
        required_dirs = ["code", "data/raw", "data/processed", "data/reports", "tests", "state"]
        
        created = create_directories(tmp_path)
        
        # Check all directories were created
        for dir_name in required_dirs:
            full_path = tmp_path / dir_name
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_create_directories_idempotent(self, tmp_path):
        """Test that calling create_directories multiple times doesn't fail."""
        create_directories(tmp_path)
        created_first = create_directories(tmp_path)
        
        # Should not raise any exceptions
        assert len(created_first) == 6

    def test_verify_directories_success(self, tmp_path):
        """Test verify_directories returns True when all directories exist."""
        create_directories(tmp_path)
        result = verify_directories(tmp_path)
        
        assert result is True

    def test_verify_directories_failure(self, tmp_path):
        """Test verify_directories returns False when directories are missing."""
        # Don't create directories, just verify
        result = verify_directories(tmp_path)
        
        assert result is False

    def test_nested_directories_created(self, tmp_path):
        """Test that nested directories (data/raw) are created with parents."""
        created = create_directories(tmp_path)
        
        # Check nested directories exist
        assert (tmp_path / "data/raw").exists()
        assert (tmp_path / "data/processed").exists()
        assert (tmp_path / "data/reports").exists()

    def test_current_directory_default(self):
        """Test that create_directories works with default (current) directory."""
        # Use a temporary directory to avoid polluting current dir
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                created = create_directories()
                
                required_dirs = ["code", "data/raw", "data/processed", "data/reports", "tests", "state"]
                for dir_name in required_dirs:
                    assert os.path.exists(dir_name), f"Directory {dir_name} was not created"
            finally:
                os.chdir(original_dir)