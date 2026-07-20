import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from code.setup_data_dirs import setup_directories


class TestSetupDataDirs:
    """Tests for the setup_data_dirs module (T004)."""

    def test_creates_required_directories(self, tmp_path):
        """Verify that all required data directories are created."""
        # Arrange
        data_raw = tmp_path / "data" / "raw"
        data_processed = tmp_path / "data" / "processed"
        data_splits = tmp_path / "data" / "splits"
        results = tmp_path / "results"

        # Act
        setup_directories(tmp_path)

        # Assert
        assert data_raw.exists() and data_raw.is_dir()
        assert data_processed.exists() and data_processed.is_dir()
        assert data_splits.exists() and data_splits.is_dir()
        assert results.exists() and results.is_dir()

    def test_does_not_fail_if_directories_exist(self, tmp_path):
        """Verify that the function handles existing directories gracefully."""
        # Arrange
        (tmp_path / "data" / "raw").mkdir(parents=True)
        
        # Act & Assert (should not raise)
        setup_directories(tmp_path)
        
        # Verify directory still exists
        assert (tmp_path / "data" / "raw").exists()

    def test_creates_parent_directories(self, tmp_path):
        """Verify that parent directories are created if missing."""
        # Arrange: Ensure 'data' does not exist
        assert not (tmp_path / "data").exists()

        # Act
        setup_directories(tmp_path)

        # Assert
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "results").exists()