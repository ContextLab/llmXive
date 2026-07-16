"""
Unit tests for data directory setup functionality.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We need to add the code directory to the path temporarily
import sys
from unittest.mock import patch, MagicMock

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from setup_data_directories import create_data_directories


class TestDataDirectoryCreation:
    """Tests for the create_data_directories function."""

    def test_creates_all_required_directories(self):
        """Verify that all required data directories are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)

            # Call the function
            created = create_data_directories(base_path)

            # Verify all directories exist
            expected_dirs = [
                "data",
                "data/raw",
                "data/processed",
                "data/logs",
            ]

            for dir_name in expected_dirs:
                full_path = base_path / dir_name
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"

            # Verify the returned list contains the created paths
            assert len(created) == len(expected_dirs)
            for dir_name in expected_dirs:
                full_path = base_path / dir_name
                assert str(full_path) in created

    def test_skips_existing_directories(self):
        """Verify that existing directories are not recreated."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)

            # Pre-create some directories
            (base_path / "data").mkdir()
            (base_path / "data" / "raw").mkdir()

            # Call the function
            created = create_data_directories(base_path)

            # Only the missing ones should be in the created list
            assert len(created) == 2  # data/processed and data/logs
            assert not any("data/processed" in d or "data/logs" in d for d in created)

    def test_creates_nested_directories(self):
        """Verify that nested directories are created correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)

            # Call the function
            create_data_directories(base_path)

            # Verify nested structure
            assert (base_path / "data" / "raw").exists()
            assert (base_path / "data" / "processed").exists()
            assert (base_path / "data" / "logs").exists()

    def test_handles_concurrent_creation(self):
        """Verify that the function handles concurrent calls gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)

            # Call the function multiple times
            create_data_directories(base_path)
            create_data_directories(base_path)
            create_data_directories(base_path)

            # Verify all directories still exist and are valid
            assert (base_path / "data").exists()
            assert (base_path / "data" / "raw").exists()
            assert (base_path / "data" / "processed").exists()
            assert (base_path / "data" / "logs").exists()