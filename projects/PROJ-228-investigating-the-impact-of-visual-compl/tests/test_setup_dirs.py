import os
import shutil
from pathlib import Path

import pytest

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from code.setup_dirs import (
    create_data_directories,
    create_test_directories,
    create_source_directories,
    create_docs_directory,
    create_all_directories,
)


class TestSetupDirs:
    """Tests for directory creation functions."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory for testing and clean up afterwards."""
        # Create a temporary root for testing to avoid cluttering the real project
        # We will run the creation in a temp dir and verify
        self.temp_root = Path("test_tmp_root")
        if self.temp_root.exists():
            shutil.rmtree(self.temp_root)
        self.temp_root.mkdir()

        # Change to temp root
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_root)

        yield

        # Restore cwd and cleanup
        os.chdir(self.original_cwd)
        if self.temp_root.exists():
            shutil.rmtree(self.temp_root)

    def test_create_source_directories(self):
        """Test that code directory is created."""
        create_source_directories()
        assert Path("code").exists()
        assert Path("code").is_dir()

    def test_create_test_directories(self):
        """Test that tests/unit and tests/integration are created."""
        create_test_directories()
        assert Path("tests").exists()
        assert Path("tests/unit").exists()
        assert Path("tests/integration").exists()

    def test_create_data_directories(self):
        """Test that data/raw, data/interim, data/results are created."""
        create_data_directories()
        assert Path("data").exists()
        assert Path("data/raw").exists()
        assert Path("data/interim").exists()
        assert Path("data/results").exists()

    def test_create_docs_directory(self):
        """Test that docs directory is created."""
        create_docs_directory()
        assert Path("docs").exists()
        assert Path("docs").is_dir()

    def test_create_all_directories(self):
        """Test that create_all_directories creates everything."""
        create_all_directories()

        # Verify code
        assert Path("code").exists()

        # Verify tests
        assert Path("tests/unit").exists()
        assert Path("tests/integration").exists()

        # Verify data
        assert Path("data/raw").exists()
        assert Path("data/interim").exists()
        assert Path("data/results").exists()

        # Verify docs
        assert Path("docs").exists()

    def test_idempotency(self):
        """Test that running create_all_directories twice does not raise errors."""
        create_all_directories()
        create_all_directories()  # Should not raise
        assert Path("code").exists()
        assert Path("data/raw").exists()