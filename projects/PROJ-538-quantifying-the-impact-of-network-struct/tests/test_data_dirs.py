"""
Tests for data directory setup functionality.
"""
import os
import tempfile
from pathlib import Path

from code.setup_data_dirs import setup_data_directories


def test_setup_data_directories_creates_structure():
    """
    Verify that setup_data_directories creates the required directory structure.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run the setup function on the temporary directory
        setup_data_directories(tmpdir)

        base = Path(tmpdir)
        data_root = base / "data"
        subdirs = ["raw", "processed", "contracts"]

        # Verify root data directory exists
        assert data_root.exists(), "data/ directory was not created"
        assert data_root.is_dir(), "data/ is not a directory"

        # Verify subdirectories exist
        for subdir_name in subdirs:
            subdir_path = data_root / subdir_name
            assert subdir_path.exists(), f"{subdir_name}/ directory was not created"
            assert subdir_path.is_dir(), f"{subdir_name}/ is not a directory"


def test_setup_data_directories_idempotent():
    """
    Verify that running setup_data_directories multiple times does not cause errors.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run twice
        setup_data_directories(tmpdir)
        setup_data_directories(tmpdir)

        base = Path(tmpdir)
        data_root = base / "data"
        assert data_root.exists()
        assert (data_root / "raw").exists()
        assert (data_root / "processed").exists()
        assert (data_root / "contracts").exists()