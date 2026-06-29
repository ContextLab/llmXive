"""
Unit tests for data directory creation.
"""

import os
import tempfile
from pathlib import Path

import pytest

from code.setup.create_data_dirs import create_data_directories


class TestDataDirectories:
    """Test suite for data directory creation functionality."""

    def test_creates_all_required_directories(self):
        """Verify that all required data directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create a dummy code/ directory to establish project structure
            (base_dir / "code").mkdir()

            # Run the function
            create_data_directories(base_dir)

            # Verify all directories exist
            assert (base_dir / "data").exists()
            assert (base_dir / "data" / "raw").exists()
            assert (base_dir / "data" / "processed").exists()
            assert (base_dir / "data" / "figures").exists()

    def test_handles_existing_directories(self):
        """Verify that existing directories are not recreated (no errors)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create a dummy code/ directory
            (base_dir / "code").mkdir()

            # Pre-create some data directories
            (base_dir / "data" / "raw").mkdir(parents=True)

            # Run the function - should not raise errors
            create_data_directories(base_dir)

            # All directories should still exist
            assert (base_dir / "data").exists()
            assert (base_dir / "data" / "raw").exists()
            assert (base_dir / "data" / "processed").exists()
            assert (base_dir / "data" / "figures").exists()

    def test_creates_nested_structure(self):
        """Verify that nested subdirectories are created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create a dummy code/ directory
            (base_dir / "code").mkdir()

            # Run the function
            create_data_directories(base_dir)

            # Verify the full nested structure
            data_path = base_dir / "data"
            assert data_path.is_dir()
            assert (data_path / "raw").is_dir()
            assert (data_path / "processed").is_dir()
            assert (data_path / "figures").is_dir()

            # Verify they are subdirectories of data/
            assert (data_path / "raw").parent == data_path
            assert (data_path / "processed").parent == data_path
            assert (data_path / "figures").parent == data_path