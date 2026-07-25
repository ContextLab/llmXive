import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Ensure the code directory is in the path for imports
code_root = Path(__file__).resolve().parents[2]
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.setup_directories import setup_data_directories, REQUIRED_DATA_DIRS

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

class TestDirectorySetup:
    """Unit tests for directory setup functionality."""

    def test_setup_creates_all_required_dirs(self, temp_config_dir):
        """Verify that all required data subdirectories are created."""
        setup_data_directories(temp_config_dir)
        
        for subdir_name in REQUIRED_DATA_DIRS:
            expected_path = temp_config_dir / subdir_name
            assert expected_path.exists(), f"Directory {expected_path} was not created"
            assert expected_path.is_dir(), f"{expected_path} is not a directory"

    def test_setup_creates_nested_structure(self, temp_config_dir):
        """Verify that nested directories are created if base doesn't exist."""
        # Start with an empty temp dir
        assert temp_config_dir.exists()
        
        # Setup should create the base if it didn't exist (though fixture ensures it does)
        # and all subdirs
        setup_data_directories(temp_config_dir)
        
        # Check specific deep paths that might be needed later
        processed_path = temp_config_dir / "processed"
        assert processed_path.exists()

    def test_setup_idempotent(self, temp_config_dir):
        """Verify that running setup multiple times doesn't cause errors."""
        setup_data_directories(temp_config_dir)
        setup_data_directories(temp_config_dir)
        
        for subdir_name in REQUIRED_DATA_DIRS:
            assert (temp_config_dir / subdir_name).exists()

    def test_required_dirs_constant(self):
        """Verify the REQUIRED_DATA_DIRS list contains the correct entries."""
        expected_dirs = {"raw", "processed", "traits", "manifests", "synthetic"}
        assert set(REQUIRED_DATA_DIRS) == expected_dirs, \
            f"REQUIRED_DATA_DIRS mismatch. Expected {expected_dirs}, got {set(REQUIRED_DATA_DIRS)}"