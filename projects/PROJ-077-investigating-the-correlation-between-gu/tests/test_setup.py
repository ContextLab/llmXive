import os
import pytest
from pathlib import Path

class TestProjectSetup:
    """Test suite for project initialization (T001)."""

    @pytest.fixture(autouse=True)
    def setup_directories(self):
        """Ensure required directories exist before tests run."""
        # This fixture ensures directories are created before any test runs
        from config import ensure_directories
        ensure_directories(["data/raw", "data/processed", "code", "tests"])
        yield

    def test_data_raw_directory_exists(self):
        """Verify data/raw directory exists."""
        assert os.path.isdir("data/raw"), "data/raw directory does not exist"

    def test_data_processed_directory_exists(self):
        """Verify data/processed directory exists."""
        assert os.path.isdir("data/processed"), "data/processed directory does not exist"

    def test_code_directory_exists(self):
        """Verify code directory exists."""
        assert os.path.isdir("code"), "code directory does not exist"

    def test_tests_directory_exists(self):
        """Verify tests directory exists."""
        assert os.path.isdir("tests"), "tests directory does not exist"

    def test_all_required_directories_exist(self):
        """Verify all required directories exist simultaneously."""
        required_dirs = ["data/raw", "data/processed", "code", "tests"]
        for dir_path in required_dirs:
            assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"