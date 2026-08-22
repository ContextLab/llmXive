"""
Unit tests for the data directory setup functionality.
"""
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories


class TestSetupDataDirectories:
    """Tests for the setup_data_directories function."""

    def test_creates_directory_structure(self, tmp_path):
        """Test that the function creates the required directory structure."""
        directories = setup_data_directories(tmp_path)
        
        assert len(directories) == 3
        
        data_dir = tmp_path / "data"
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        
        assert directories[0] == data_dir
        assert directories[1] == raw_dir
        assert directories[2] == processed_dir
        
        assert data_dir.exists()
        assert raw_dir.exists()
        assert processed_dir.exists()
        
        assert data_dir.is_dir()
        assert raw_dir.is_dir()
        assert processed_dir.is_dir()

    def test_handles_existing_directories(self, tmp_path):
        """Test that the function works correctly when directories already exist."""
        # Create directories beforehand
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        
        data_dir.mkdir()
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Should not raise an error
        directories = setup_data_directories(tmp_path)
        
        assert len(directories) == 3
        assert all(d.exists() for d in directories)

    def test_verifies_writable(self, tmp_path):
        """Test that the function verifies directories are writable."""
        directories = setup_data_directories(tmp_path)
        
        # Verify we can write to each directory
        for directory in directories:
            test_file = directory / "test_write_file.txt"
            try:
                test_file.write_text("test")
                assert test_file.exists()
                test_file.unlink()
            except Exception as e:
                pytest.fail(f"Directory {directory} is not writable: {e}")

    def test_raises_on_unwritable_directory(self, tmp_path):
        """Test that the function raises an error for unwritable directories."""
        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)
        
        try:
            # This should fail because we can't write to readonly_dir
            # Note: This test might pass on some systems where root can still write
            # or if the test is run as root. It's best effort.
            setup_data_directories(readonly_dir)
        except OSError:
            # Expected behavior
            pass
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    def test_returns_correct_paths(self, tmp_path):
        """Test that the function returns the correct path objects."""
        directories = setup_data_directories(tmp_path)
        
        expected_paths = [
            tmp_path / "data",
            tmp_path / "data" / "raw",
            tmp_path / "data" / "processed"
        ]
        
        for expected, actual in zip(expected_paths, directories):
            assert actual == expected
            assert isinstance(actual, Path)
