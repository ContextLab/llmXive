"""
Unit tests for setup_data_directories.py.
Verifies that the data directories are created and exist as expected.
"""
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path to import the module
# Assuming this test file is in code/tests/unit/
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_data_directories import setup_data_directories, PROJECT_ROOT


class TestDataDirectories:
    """Test suite for data directory setup functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Setup: Ensure we are in a clean state (optional, usually handled by CI).
        Teardown: Not strictly needed as we don't delete system dirs, 
        but we ensure the fixture runs.
        """
        # Save original PROJECT_ROOT if needed for complex mocking
        self.original_root = PROJECT_ROOT
        yield
        # Restore if modified
        # (In this simple implementation, PROJECT_ROOT is a constant, so no restore needed)

    def test_directory_creation(self):
        """
        Test that setup_data_directories creates the required directories.
        """
        # The function creates directories relative to PROJECT_ROOT
        # We assume PROJECT_ROOT is set correctly in the environment.
        # In a real test, we might mock PROJECT_ROOT to a temp dir,
        # but the requirement is to verify os.path.isdir on the real paths.
        
        # Run the setup
        result = setup_data_directories()
        
        assert result is True, "setup_data_directories should return True on success"

    def test_data_raw_exists(self):
        """
        Verify that data/raw/ directory exists after setup.
        """
        setup_data_directories()
        raw_path = PROJECT_ROOT / "data" / "raw"
        assert os.path.isdir(raw_path), f"Directory {raw_path} should exist and be a directory"

    def test_data_processed_exists(self):
        """
        Verify that data/processed/ directory exists after setup.
        """
        setup_data_directories()
        processed_path = PROJECT_ROOT / "data" / "processed"
        assert os.path.isdir(processed_path), f"Directory {processed_path} should exist and be a directory"

    def test_data_models_exists(self):
        """
        Verify that data/models/ directory exists after setup.
        """
        setup_data_directories()
        models_path = PROJECT_ROOT / "data" / "models"
        assert os.path.isdir(models_path), f"Directory {models_path} should exist and be a directory"

    def test_all_directories_verified(self):
        """
        Comprehensive check that all required data directories exist.
        """
        setup_data_directories()
        
        required_dirs = [
            "raw",
            "processed",
            "models"
        ]
        
        for dir_name in required_dirs:
            dir_path = PROJECT_ROOT / "data" / dir_name
            assert os.path.isdir(dir_path), f"Directory {dir_path} must exist"
            assert dir_path.exists(), f"Directory {dir_path} must exist"