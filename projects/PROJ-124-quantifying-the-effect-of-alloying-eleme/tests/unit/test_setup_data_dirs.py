"""
Unit tests for the setup_data_dirs module (T004a).
Verifies that data/raw and data/processed directories are created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path
from code.utils.setup_data_dirs import create_data_directories


def test_create_data_directories_creates_raw_and_processed():
    """Test that the function creates data/raw and data/processed."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        result = create_data_directories(base_path)

        assert result is True, "create_data_directories should return True on success"

        raw_dir = base_path / "data" / "raw"
        processed_dir = base_path / "data" / "processed"

        assert raw_dir.exists(), "data/raw directory should exist"
        assert raw_dir.is_dir(), "data/raw should be a directory"

        assert processed_dir.exists(), "data/processed directory should exist"
        assert processed_dir.is_dir(), "data/processed should be a directory"


def test_create_data_directories_idempotent():
    """Test that running the function twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)

        # Run twice
        result1 = create_data_directories(base_path)
        result2 = create_data_directories(base_path)

        assert result1 is True
        assert result2 is True

        raw_dir = base_path / "data" / "raw"
        processed_dir = base_path / "data" / "processed"

        assert raw_dir.exists()
        assert processed_dir.exists()


def test_create_data_directories_creates_other_required_dirs():
    """Test that other required directories are also created."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        result = create_data_directories(base_path)

        assert result is True

        # Check a few other required directories
        state_dir = base_path / "state"
        output_dir = base_path / "output"
        logs_dir = base_path / "logs"

        assert state_dir.exists()
        assert output_dir.exists()
        assert logs_dir.exists()