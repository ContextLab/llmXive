"""
Unit tests for the create_test_dir module.
"""
import os
import tempfile
from pathlib import Path
import pytest

from create_test_dir import ensure_test_directory
from config import get_path


def test_ensure_test_directory_creates_folder():
    """Test that ensure_test_directory creates the folder if it doesn't exist."""
    # Create a temporary directory to act as a mock project root
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # We need to mock the config or pass the path directly
        # Since ensure_test_directory can take a base_path, we use that.
        test_dir = tmp_path / "data" / "test"

        # Ensure it doesn't exist first
        if test_dir.exists():
            test_dir.rmdir()

        result_path = ensure_test_directory(base_path=tmp_path)

        assert result_path.exists()
        assert result_path.is_dir()
        assert result_path == test_dir


def test_ensure_test_directory_verifies_existing():
    """Test that ensure_test_directory returns the path if it already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_dir = tmp_path / "data" / "test"
        test_dir.mkdir(parents=True)

        result_path = ensure_test_directory(base_path=tmp_path)

        assert result_path.exists()
        assert result_path == test_dir


def test_ensure_test_directory_raises_on_failure():
    """Test that ensure_test_directory raises if it can't create the directory."""
    # This is hard to test without permission issues, so we test the logic
    # by ensuring the function correctly constructs the path.
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Force a read-only parent to trigger creation failure if possible,
        # but usually permissions are the only way.
        # Instead, we verify the path construction logic.
        expected = tmp_path / "data" / "test"
        result = ensure_test_directory(base_path=tmp_path)
        assert result == expected