"""
Unit tests for the setup_directories module.

These tests verify that the directory structure is created correctly
and that the setup script handles edge cases appropriately.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Import the function to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from setup_directories import setup_directories


class TestSetupDirectories:
    """Test cases for setup_directories function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify all standard directories are created."""
        expected_dirs = [
            "data/raw",
            "data/processed",
            "data/interim",
            "data/results",
            "code",
            "tests",
            "state",
            "figures",
        ]

        result = setup_directories(str(tmp_path))

        assert result is True
        for dir_path in expected_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} exists but is not a directory"

    def test_skips_existing_directories(self, tmp_path):
        """Verify the function handles pre-existing directories gracefully."""
        # Create one directory beforehand
        pre_existing = tmp_path / "code"
        pre_existing.mkdir(parents=True)

        result = setup_directories(str(tmp_path))

        assert result is True
        assert pre_existing.exists()

    def test_fails_on_file_collision(self, tmp_path):
        """Verify the function fails when a path exists as a file."""
        # Create a file where a directory should be
        collision_path = tmp_path / "code"
        collision_path.touch()

        result = setup_directories(str(tmp_path))

        assert result is False

    def test_creates_nested_directories(self, tmp_path):
        """Verify nested directories are created (parents=True behavior)."""
        result = setup_directories(str(tmp_path))

        assert result is True
        # Verify a deeply nested path was created
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()

    def test_returns_true_on_success(self, tmp_path):
        """Verify the function returns True when all directories are created."""
        result = setup_directories(str(tmp_path))
        assert result is True

    def test_handles_relative_path(self, tmp_path):
        """Verify the function works with relative paths."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = setup_directories(".")
            assert result is True
            assert (tmp_path / "code").exists()
        finally:
            os.chdir(original_cwd)