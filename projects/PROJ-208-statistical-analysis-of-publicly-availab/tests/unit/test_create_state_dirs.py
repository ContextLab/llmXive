"""
Unit tests for state directory creation.
"""
import os
import tempfile
from pathlib import Path
import pytest

from setup.create_state_dirs import create_state_directories


class TestCreateStateDirs:
    """Tests for create_state_directories function."""

    def test_creates_state_directory(self, tmp_path):
        """Test that state/ directory is created."""
        create_state_directories(str(tmp_path))
        state_dir = tmp_path / "state"
        assert state_dir.exists()
        assert state_dir.is_dir()

    def test_creates_projects_subdirectory(self, tmp_path):
        """Test that state/projects/ subdirectory is created."""
        create_state_directories(str(tmp_path))
        projects_dir = tmp_path / "state" / "projects"
        assert projects_dir.exists()
        assert projects_dir.is_dir()

    def test_idempotent_when_exists(self, tmp_path):
        """Test that calling twice doesn't error when dirs exist."""
        # First call creates directories
        create_state_directories(str(tmp_path))
        # Second call should not raise
        create_state_directories(str(tmp_path))
        state_dir = tmp_path / "state"
        assert state_dir.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if needed."""
        # Start with empty tmp_path
        assert not (tmp_path / "state").exists()
        create_state_directories(str(tmp_path))
        assert (tmp_path / "state").exists()
        assert (tmp_path / "state" / "projects").exists()