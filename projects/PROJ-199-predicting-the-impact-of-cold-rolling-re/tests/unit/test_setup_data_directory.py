import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add the project root to the path to allow imports
# Assuming this test file is in tests/unit/, and code/ is at the root
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.setup_data_directory import ensure_data_directory, verify_data_directory

class TestDataDirectorySetup:
    """
    Tests for the data directory setup functionality (Task T001b).
    """

    def test_ensure_creates_directory_if_missing(self, tmp_path):
        """
        Test that ensure_data_directory creates the 'data' directory if it doesn't exist.
        """
        # tmp_path provides a unique temporary directory for this test
        data_dir = tmp_path / "data"
        
        # Ensure the directory is created
        result_path = ensure_data_directory(base_path=tmp_path)
        
        # Verify the returned path matches the expected data directory
        assert result_path == data_dir
        # Verify the directory actually exists on disk
        assert data_dir.is_dir()
        # Verify .gitkeep was created
        assert (data_dir / ".gitkeep").exists()

    def test_ensure_uses_existing_directory(self, tmp_path):
        """
        Test that ensure_data_directory does not fail if the directory already exists.
        """
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Call ensure on an existing directory
        result_path = ensure_data_directory(base_path=tmp_path)
        
        assert result_path == data_dir
        assert data_dir.is_dir()

    def test_verify_returns_true_when_exists(self, tmp_path):
        """
        Test that verify_data_directory returns True when the directory exists.
        """
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        assert verify_data_directory(base_path=tmp_path) is True

    def test_verify_returns_false_when_missing(self, tmp_path):
        """
        Test that verify_data_directory returns False when the directory is missing.
        """
        # Ensure 'data' does not exist in tmp_path
        assert not (tmp_path / "data").exists()
        
        assert verify_data_directory(base_path=tmp_path) is False

    def test_verification_logic_matches_spec(self, tmp_path):
        """
        Test that the verification logic matches the specific requirement:
        `pathlib.Path(__file__).parent.joinpath('data').is_dir()`
        (Adapted for the test's base_path context).
        """
        data_dir = tmp_path / "data"
        
        # Case 1: Directory missing
        assert not data_dir.is_dir()
        assert verify_data_directory(base_path=tmp_path) is False
        
        # Case 2: Directory created
        data_dir.mkdir()
        assert data_dir.is_dir()
        assert verify_data_directory(base_path=tmp_path) is True
        
        # Case 3: Directory removed
        shutil.rmtree(data_dir)
        assert not data_dir.is_dir()
        assert verify_data_directory(base_path=tmp_path) is False