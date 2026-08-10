import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_data_dirs import create_directories, RAW_DIR, GENERATED_DIR, ANALYSIS_DIR

class TestDataDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """Setup and teardown for each test."""
        # Create a temporary project structure
        self.temp_root = tmp_path
        self.temp_data_dir = self.temp_root / "data"
        self.temp_raw_dir = self.temp_data_dir / "raw"
        self.temp_generated_dir = self.temp_data_dir / "generated"
        self.temp_analysis_dir = self.temp_data_dir / "analysis"

        # Mock the module-level constants to use our temp directory
        import setup_data_dirs
        original_data_dir = setup_data_dirs.DATA_DIR
        original_raw_dir = setup_data_dirs.RAW_DIR
        original_generated_dir = setup_data_dirs.GENERATED_DIR
        original_analysis_dir = setup_data_dirs.ANALYSIS_DIR

        setup_data_dirs.DATA_DIR = str(self.temp_data_dir)
        setup_data_dirs.RAW_DIR = str(self.temp_raw_dir)
        setup_data_dirs.GENERATED_DIR = str(self.temp_generated_dir)
        setup_data_dirs.ANALYSIS_DIR = str(self.temp_analysis_dir)

        yield

        # Restore original values
        setup_data_dirs.DATA_DIR = original_data_dir
        setup_data_dirs.RAW_DIR = original_raw_dir
        setup_data_dirs.GENERATED_DIR = original_generated_dir
        setup_data_dirs.ANALYSIS_DIR = original_analysis_dir

    def test_create_directories_creates_all_required_dirs(self):
        """Test that create_directories creates raw, generated, and analysis directories."""
        # Ensure directories don't exist initially
        assert not self.temp_raw_dir.exists()
        assert not self.temp_generated_dir.exists()
        assert not self.temp_analysis_dir.exists()

        # Run the function
        result = create_directories()

        # Assert result is True
        assert result is True

        # Assert all directories were created
        assert self.temp_raw_dir.exists()
        assert self.temp_raw_dir.is_dir()
        assert self.temp_generated_dir.exists()
        assert self.temp_generated_dir.is_dir()
        assert self.temp_analysis_dir.exists()
        assert self.temp_analysis_dir.is_dir()

    def test_create_directories_handles_existing_dirs(self):
        """Test that create_directories doesn't fail if directories already exist."""
        # Create directories beforehand
        self.temp_raw_dir.mkdir(parents=True)
        self.temp_generated_dir.mkdir(parents=True)
        self.temp_analysis_dir.mkdir(parents=True)

        # Run the function - should not raise
        result = create_directories()

        # Assert result is True
        assert result is True

    def test_state_dir_not_created(self):
        """Test that the state directory is NOT created by this function."""
        state_dir = self.temp_root / "state"

        # Ensure state dir doesn't exist
        assert not state_dir.exists()

        # Run the function
        create_directories()

        # Assert state dir still doesn't exist (T008 should not create it)
        assert not state_dir.exists()

    def test_directories_are_within_data_folder(self):
        """Test that all created directories are inside the data folder."""
        create_directories()

        # Verify parent is data dir
        assert self.temp_raw_dir.parent == self.temp_data_dir
        assert self.temp_generated_dir.parent == self.temp_data_dir
        assert self.temp_analysis_dir.parent == self.temp_data_dir
