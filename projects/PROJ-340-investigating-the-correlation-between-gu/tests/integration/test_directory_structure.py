"""
Integration test to verify the data directory structure exists.
"""
import os
import pytest
from pathlib import Path


class TestDataDirectoryStructure:
    """Tests for the required data directory structure."""

    @pytest.fixture(autouse=True)
    def setup_dirs(self):
        """Ensure directories exist before testing."""
        from code.setup_data_dirs import setup_data_directories
        setup_data_directories()

    def test_data_root_exists(self):
        """Verify the data/ root directory exists."""
        assert Path("data").exists(), "data/ directory does not exist"

    def test_raw_directory_exists(self):
        """Verify data/raw/ directory exists."""
        assert Path("data/raw").exists(), "data/raw/ directory does not exist"

    def test_processed_directory_exists(self):
        """Verify data/processed/ directory exists."""
        assert Path("data/processed").exists(), "data/processed/ directory does not exist"

    def test_results_directory_exists(self):
        """Verify data/results/ directory exists."""
        assert Path("data/results").exists(), "data/results/ directory does not exist"

    def test_config_directory_exists(self):
        """Verify data/config/ directory exists."""
        assert Path("data/config").exists(), "data/config/ directory does not exist"

    def test_all_directories_are_writable(self):
        """Verify all directories are writable by creating a temp file."""
        dirs = ["data", "data/raw", "data/processed", "data/results", "data/config"]
        for dir_path in dirs:
            test_file = Path(dir_path) / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                pytest.fail(f"Directory {dir_path} is not writable: {e}")
