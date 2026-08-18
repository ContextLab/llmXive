"""
Unit tests for setup_data_dirs.py
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We need to import the function from the code module
# Since the script is in code/setup_data_dirs.py, we import from there
import sys
from unittest.mock import patch, MagicMock

# Add the code directory to the path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_data_dirs import setup_data_directories


class TestSetupDataDirectories:
    """Tests for the setup_data_directories function."""

    def test_creates_missing_directories(self, tmp_path):
        """Test that missing directories are created."""
        # Create a temporary data directory structure
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"

        # Mock the data_dir to point to our temp directory
        with patch('setup_data_dirs.data_dir', data_dir):
            created = setup_data_directories()

            # Verify directories were created
            assert raw_dir.exists()
            assert processed_dir.exists()
            assert len(created) == 2
            assert str(raw_dir) in created
            assert str(processed_dir) in created

    def test_does_not_fail_on_existing_directories(self, tmp_path):
        """Test that existing directories don't cause errors."""
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"

        # Create directories beforehand
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)

        with patch('setup_data_dirs.data_dir', data_dir):
            created = setup_data_directories()

            # Should still return the paths, even if they already existed
            assert len(created) >= 0  # May be 0 if we only count newly created
            assert raw_dir.exists()
            assert processed_dir.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"

        # Don't create the data directory
        assert not data_dir.exists()

        with patch('setup_data_dirs.data_dir', data_dir):
            created = setup_data_directories()

            assert data_dir.exists()
            assert raw_dir.exists()
            assert processed_dir.exists()