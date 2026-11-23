"""
Unit tests for the data directory creation functionality.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from data_setup.create_data_dirs import create_data_directories


class TestDataDirectoryCreation:
    """Tests for create_data_directories function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        create_data_directories(tmp_path)

        expected_dirs = [
            tmp_path / "data",
            tmp_path / "data" / "raw",
            tmp_path / "data" / "derived",
            tmp_path / "data" / "aggregated",
        ]

        for directory in expected_dirs:
            assert directory.exists(), f"Directory {directory} was not created"
            assert directory.is_dir(), f"{directory} is not a directory"

    def test_idempotent_operation(self, tmp_path):
        """Verify that running the function twice does not cause errors."""
        # First run
        create_data_directories(tmp_path)

        # Second run
        create_data_directories(tmp_path)

        # Verify directories still exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "derived").exists()
        assert (tmp_path / "data" / "aggregated").exists()

    def test_handles_existing_directories(self, tmp_path):
        """Verify that pre-existing directories are not overwritten or cause errors."""
        # Create the structure manually first
        (tmp_path / "data" / "raw").mkdir(parents=True)

        # Run the function
        create_data_directories(tmp_path)

        # Verify the manually created directory still exists
        assert (tmp_path / "data" / "raw").exists()

    def test_creates_parent_directories(self, tmp_path):
        """Verify that parent directories are created if missing."""
        # Start with an empty tmp_path (no data directory)
        create_data_directories(tmp_path)

        # Verify the full hierarchy exists
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "derived").exists()
        assert (tmp_path / "data" / "aggregated").exists()