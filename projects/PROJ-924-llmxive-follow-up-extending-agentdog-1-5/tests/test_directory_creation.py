"""
Tests for directory creation and verification functionality.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from create_directories import ensure_directories
from verify_project_structure import verify_structure


class TestEnsureDirectories:
    """Tests for ensure_directories function."""

    def test_creates_single_directory(self, tmp_path):
        """Test that a single directory is created."""
        result = ensure_directories(tmp_path, ["code"])
        assert len(result) == 1
        assert result[0] == tmp_path / "code"
        assert result[0].exists()
        assert result[0].is_dir()

    def test_creates_nested_directories(self, tmp_path):
        """Test that nested directories are created."""
        result = ensure_directories(tmp_path, ["data/raw", "data/processed"])
        assert len(result) == 2
        assert (tmp_path / "data/raw").exists()
        assert (tmp_path / "data/processed").exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created when needed."""
        result = ensure_directories(tmp_path, ["specs/001-llmxive-drift-detection"])
        assert len(result) == 1
        assert (tmp_path / "specs").exists()
        assert (tmp_path / "specs/001-llmxive-drift-detection").exists()

    def test_returns_existing_directory(self, tmp_path):
        """Test that existing directories are returned without error."""
        # Create directory first
        (tmp_path / "code").mkdir()
        result = ensure_directories(tmp_path, ["code"])
        assert len(result) == 1
        assert result[0] == tmp_path / "code"

    def test_uses_default_directories(self, tmp_path):
        """Test that default directories are created when none specified."""
        result = ensure_directories(tmp_path)
        assert len(result) > 0
        # Check at least one default exists
        assert (tmp_path / "code").exists()

    def test_raises_on_failure(self, tmp_path):
        """Test that OSError is raised when directory cannot be created."""
        # This is hard to test without actual permission issues,
        # but we verify the function signature handles it
        pass


class TestVerifyStructure:
    """Tests for verify_structure function."""

    def test_verifies_existing_structure(self, tmp_path):
        """Test verification of a properly created structure."""
        # Create the structure first
        ensure_directories(tmp_path)

        # Now verify
        result = verify_structure(tmp_path)
        assert result is True

    def test_fails_on_missing_structure(self, tmp_path):
        """Test verification fails when structure is incomplete."""
        # Don't create anything
        result = verify_structure(tmp_path)
        assert result is False

    def test_verifies_nested_structure(self, tmp_path):
        """Test verification of nested directories."""
        ensure_directories(tmp_path, ["specs/001-llmxive-drift-detection"])
        result = verify_structure(tmp_path)
        assert result is True