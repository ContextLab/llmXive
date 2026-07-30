import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import create_directories, verify_directories

class TestSetupProject:
    def test_create_directories_creates_all_required(self, tmp_path):
        """Test that create_directories creates all required folders."""
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/reports",
            "tests",
            "state"
        ]
        
        created_paths = create_directories(tmp_path)
        
        assert len(created_paths) == len(required_dirs)
        
        for dir_name in required_dirs:
            expected_path = tmp_path / dir_name
            assert expected_path.is_dir()
            assert expected_path in created_paths

    def test_verify_directories_returns_true_when_all_exist(self, tmp_path):
        """Test verify_directories returns True when all dirs exist."""
        # First create them
        create_directories(tmp_path)
        
        # Then verify
        assert verify_directories(tmp_path) is True

    def test_verify_directories_returns_false_when_missing(self, tmp_path):
        """Test verify_directories returns False when some dirs are missing."""
        # Only create a subset
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        
        # Verify should fail because data/processed, etc. are missing
        assert verify_directories(tmp_path) is False

    def test_create_directories_with_nested_paths(self, tmp_path):
        """Test that nested paths (e.g., data/raw) are created correctly."""
        created_paths = create_directories(tmp_path)
        
        data_raw_path = tmp_path / "data" / "raw"
        assert data_raw_path.is_dir()
        
        data_processed_path = tmp_path / "data" / "processed"
        assert data_processed_path.is_dir()

    def test_create_directories_idempotent(self, tmp_path):
        """Test that calling create_directories multiple times is safe."""
        first_run = create_directories(tmp_path)
        second_run = create_directories(tmp_path)
        
        # Should return the same paths
        assert first_run == second_run
        
        # All dirs should still exist
        assert verify_directories(tmp_path) is True