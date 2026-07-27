"""
Unit tests for directory management utilities.
"""
import os
import tempfile
from pathlib import Path
import pytest

from utils.directories import ensure_data_directories


class TestEnsureDataDirectories:
    def test_creates_required_structure(self, tmp_path):
        """Test that the function creates raw, processed, and results directories."""
        data_root = tmp_path / "data"
        expected_dirs = [
            data_root / "raw",
            data_root / "processed",
            data_root / "results",
        ]

        result = ensure_data_directories(tmp_path)

        assert len(result) == 3
        for expected in expected_dirs:
            assert expected in result
            assert expected.exists()
            assert expected.is_dir()

    def test_idempotent(self, tmp_path):
        """Test that running the function twice does not raise errors."""
        ensure_data_directories(tmp_path)
        # Run again - should not raise
        result = ensure_data_directories(tmp_path)
        assert len(result) == 3

    def test_creates_parents(self, tmp_path):
        """Test that nested parents are created if missing."""
        # Ensure 'data' doesn't exist yet
        assert not (tmp_path / "data").exists()

        result = ensure_data_directories(tmp_path)

        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()

    def test_verifies_writability(self, tmp_path, monkeypatch):
        """Test that the function fails if the directory is not writable."""
        # Create a read-only directory scenario
        readonly_dir = tmp_path / "readonly_data"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        try:
            with pytest.raises(RuntimeError, match="Failed to create or verify"):
                ensure_data_directories(readonly_dir)
        finally:
            # Restore permissions so cleanup works
            readonly_dir.chmod(0o755)

    def test_returns_path_objects(self, tmp_path):
        """Test that return values are Path objects."""
        result = ensure_data_directories(tmp_path)
        for p in result:
            assert isinstance(p, Path)