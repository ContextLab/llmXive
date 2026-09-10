import os
import pytest
from pathlib import Path
import tempfile
import shutil

from code.setup_tests import setup_tests_directories


class TestSetupTestsDirectories:
    """Unit tests for the tests directory setup functionality."""

    def test_creates_tests_directory(self, tmp_path):
        """Verify that the tests/ directory is created."""
        result = setup_tests_directories(tmp_path)
        
        assert len(result) == 3
        assert (tmp_path / "tests").exists()
        assert (tmp_path / "tests").is_dir()

    def test_creates_unit_subdirectory(self, tmp_path):
        """Verify that the tests/unit/ subdirectory is created."""
        result = setup_tests_directories(tmp_path)
        
        unit_dir = tmp_path / "tests" / "unit"
        assert unit_dir.exists()
        assert unit_dir.is_dir()
        assert unit_dir in result

    def test_creates_integration_subdirectory(self, tmp_path):
        """Verify that the tests/integration/ subdirectory is created."""
        result = setup_tests_directories(tmp_path)
        
        integration_dir = tmp_path / "tests" / "integration"
        assert integration_dir.exists()
        assert integration_dir.is_dir()
        assert integration_dir in result

    def test_directories_are_writable(self, tmp_path):
        """Verify that created directories are writable."""
        result = setup_tests_directories(tmp_path)
        
        for dir_path in result:
            test_file = dir_path / "write_test.txt"
            try:
                test_file.write_text("test")
                assert test_file.read_text() == "test"
            finally:
                if test_file.exists():
                    test_file.unlink()

    def test_idempotent_when_existing(self, tmp_path):
        """Verify that running setup again doesn't fail on existing dirs."""
        # Create the structure manually first
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "unit").mkdir()
        (tmp_path / "tests" / "integration").mkdir()
        
        # Running setup should succeed and not raise
        result = setup_tests_directories(tmp_path)
        assert len(result) == 3

    def test_uses_absolute_paths(self, tmp_path):
        """Verify that returned paths are absolute."""
        result = setup_tests_directories(tmp_path)
        
        for dir_path in result:
            assert dir_path.is_absolute()
