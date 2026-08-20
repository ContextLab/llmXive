"""
Tests for the directory structure initialization module (setup_dirs.py).
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from setup_dirs import create_directories

class TestSetupDirs:
    """Test cases for directory creation functionality."""

    def test_creates_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        # Define expected relative paths
        expected_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "outputs",
            "tests"
        ]

        # Call the function with a temporary directory
        create_directories(tmp_path)

        # Verify each directory was created
        for rel_dir in expected_dirs:
            full_path = tmp_path / rel_dir
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} exists but is not a directory"

    def test_handles_existing_directories(self, tmp_path):
        """Verify that the function doesn't fail if directories already exist."""
        # Pre-create one of the required directories
        pre_created = tmp_path / "code"
        pre_created.mkdir(parents=True)

        # The function should not raise an error
        create_directories(tmp_path)

        # Verify the directory still exists
        assert pre_created.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Verify that parent directories are created if they don't exist."""
        # Don't pre-create 'data' or 'raw'
        create_directories(tmp_path)

        # Verify the nested structure exists
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()

    def test_uses_cwd_when_no_base_path_provided(self):
        """Verify behavior when called without arguments (uses current working directory)."""
        # This test is harder to verify without side effects,
        # so we primarily ensure it doesn't crash in a controlled environment.
        # In a real scenario, we might mock Path.cwd() and check calls.
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                # Mock Path.cwd to return our temp dir to avoid polluting real cwd
                with patch('setup_dirs.Path.cwd', return_value=Path(tmp_dir)):
                    create_directories()
                
                # Verify directories were created in temp dir
                assert (Path(tmp_dir) / "code").exists()
            finally:
                os.chdir(original_cwd)
