"""
Tests for the setup_data_dirs.py script to ensure directories are created correctly.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_data_dirs import create_directory, main

class TestDataDirsSetup:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory to simulate project root."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        yield
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_create_directory_creates_folder(self):
        """Test that create_directory creates a new folder."""
        test_path = Path(self.temp_dir) / "test_new_dir"
        assert not test_path.exists()
        create_directory(test_path)
        assert test_path.exists()
        assert test_path.is_dir()

    def test_create_directory_idempotent(self):
        """Test that creating an existing directory does not fail."""
        test_path = Path(self.temp_dir) / "existing_dir"
        test_path.mkdir()
        create_directory(test_path)
        assert test_path.exists()

    def test_main_creates_all_data_dirs(self):
        """Test that main() creates the required data subdirectories."""
        # Run the main function
        result = main()
        assert result == 0

        # Check that the data directory exists
        data_dir = Path(self.temp_dir) / "data"
        assert data_dir.exists()
        assert data_dir.is_dir()

        # Check specific subdirectories
        required_subdirs = ["raw", "processed", "synthetic", "derivation_logs"]
        for subdir in required_subdirs:
            subdir_path = data_dir / subdir
            assert subdir_path.exists(), f"Missing directory: {subdir_path}"
            assert subdir_path.is_dir(), f"Not a directory: {subdir_path}"