"""
Tests for T001b: Data directory creation.
"""
import os
import tempfile
from pathlib import Path

import pytest

# Import the function under test
import sys
from code.setup_data_directories import create_data_directories, main


class TestDataDirectories:
    """Test cases for data directory creation."""

    def test_create_directories_returns_dict(self, tmp_path):
        """Test that create_directories returns a dictionary of paths."""
        # Change to a temporary directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Create a mock data directory structure
        data_root = tmp_path / "data"
        data_root.mkdir()

        # Mock the Path resolution to use tmp_path
        import code.setup_data_directories as module
        original_resolve = Path.resolve

        def mock_resolve(self):
            if str(self) == str(Path(__file__).parent.parent):
                return tmp_path
            return original_resolve(self)

        Path.resolve = mock_resolve

        try:
            result = create_data_directories()
            assert isinstance(result, dict)
            assert "raw-fmri" in result
            assert "processed-fmri" in result
            assert "behavioral" in result
            assert "results" in result
        finally:
            Path.resolve = original_resolve
            os.chdir(original_cwd)

    def test_directories_are_created(self, tmp_path):
        """Test that all required directories are actually created."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        data_root = tmp_path / "data"
        data_root.mkdir()

        import code.setup_data_directories as module
        original_resolve = Path.resolve

        def mock_resolve(self):
            if str(self) == str(Path(__file__).parent.parent):
                return tmp_path
            return original_resolve(self)

        Path.resolve = mock_resolve

        try:
            create_data_directories()

            assert (tmp_path / "data" / "raw-fmri").is_dir()
            assert (tmp_path / "data" / "processed-fmri").is_dir()
            assert (tmp_path / "data" / "behavioral").is_dir()
            assert (tmp_path / "data" / "results").is_dir()
        finally:
            Path.resolve = original_resolve
            os.chdir(original_cwd)

    def test_main_executes_without_error(self, tmp_path):
        """Test that main() runs without raising exceptions."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        data_root = tmp_path / "data"
        data_root.mkdir()

        import code.setup_data_directories as module
        original_resolve = Path.resolve

        def mock_resolve(self):
            if str(self) == str(Path(__file__).parent.parent):
                return tmp_path
            return original_resolve(self)

        Path.resolve = mock_resolve

        try:
            # This should not raise an exception
            main()
        finally:
            Path.resolve = original_resolve
            os.chdir(original_cwd)