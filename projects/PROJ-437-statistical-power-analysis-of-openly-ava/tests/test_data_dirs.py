"""
Unit tests for data directory creation (T001c).
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# Assuming the module structure: code/data_setup/create_data_dirs.py
# We need to add the code directory to the path to import it
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from data_setup.create_data_dirs import create_data_directories


def test_create_data_directories_creates_all_required():
    """Test that all required data directories are created."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        # Ensure 'code' directory exists to simulate project structure
        (base_path / "code").mkdir()

        created = create_data_directories(base_path)

        # Check all expected directories were created
        expected = [
            base_path / "data",
            base_path / "data" / "raw",
            base_path / "data" / "derived",
            base_path / "data" / "aggregated",
        ]

        assert len(created) == len(expected), f"Expected {len(expected)} directories, got {len(created)}"

        for exp_path in expected:
            assert exp_path.exists(), f"Directory {exp_path} was not created"
            assert exp_path.is_dir(), f"{exp_path} exists but is not a directory"


def test_create_data_directories_idempotent():
    """Test that running the function twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        (base_path / "code").mkdir()

        # Run twice
        create_data_directories(base_path)
        create_data_directories(base_path)

        # Verify directories still exist
        assert (base_path / "data").exists()
        assert (base_path / "data" / "raw").exists()
        assert (base_path / "data" / "derived").exists()
        assert (base_path / "data" / "aggregated").exists()


def test_create_data_directories_custom_path():
    """Test creating directories with a custom base path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        custom_base = Path(tmp_dir) / "my_project"
        custom_base.mkdir()
        (custom_base / "code").mkdir()

        created = create_data_directories(custom_base)

        expected = custom_base / "data"
        assert expected.exists()
        assert (expected / "raw").exists()