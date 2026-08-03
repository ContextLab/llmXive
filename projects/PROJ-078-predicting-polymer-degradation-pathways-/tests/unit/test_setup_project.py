import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
# Assuming setup_project is in the code directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_project import create_directories, verify_directories

class TestSetupProject:
    """Tests for project directory creation and verification."""

    def test_create_directories_creates_all_required(self, tmp_path):
        """Test that create_directories creates all required folders."""
        required = ["code", "data/raw", "data/processed", "data/reports", "tests", "state"]
        
        created = create_directories(tmp_path)
        
        assert len(created) == len(required)
        
        for rel_path in required:
            full_path = tmp_path / rel_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_verify_directories_returns_true_when_all_exist(self, tmp_path):
        """Test verify_directories returns True when all directories exist."""
        create_directories(tmp_path)
        assert verify_directories(tmp_path) is True

    def test_verify_directories_returns_false_when_missing(self, tmp_path):
        """Test verify_directories returns False when a directory is missing."""
        # Create some but not all directories
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        # Missing: data/raw, data/processed, etc.
        
        assert verify_directories(tmp_path) is False

    def test_create_directories_idempotent(self, tmp_path):
        """Test that calling create_directories twice doesn't raise errors."""
        first_run = create_directories(tmp_path)
        second_run = create_directories(tmp_path)
        
        # Second run should return empty list (no new dirs)
        assert len(second_run) == 0
        
        # Verify all still exist
        assert verify_directories(tmp_path) is True
