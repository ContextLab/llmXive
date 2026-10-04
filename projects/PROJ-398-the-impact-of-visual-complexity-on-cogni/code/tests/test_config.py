"""
Tests for the configuration module.
"""
import os
import sys
from pathlib import Path
import pytest

# Ensure code directory is in path
code_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_dir))

from src.config import GLOBAL_SEED, PROJECT_ROOT, DATA_DIR, ensure_directories_exist, METRICS_CSV_PATH


class TestConfigSeed:
    """Tests for the global random seed configuration."""

    def test_seed_defined(self):
        """Verify that GLOBAL_SEED is defined and is an integer."""
        assert GLOBAL_SEED is not None, "GLOBAL_SEED must be defined"
        assert isinstance(GLOBAL_SEED, int), "GLOBAL_SEED must be an integer"
        assert GLOBAL_SEED >= 0, "GLOBAL_SEED must be non-negative"

    def test_seed_value(self):
        """Verify the specific value of GLOBAL_SEED."""
        # Common default seed is 42
        assert GLOBAL_SEED == 42, f"Expected GLOBAL_SEED to be 42, got {GLOBAL_SEED}"


class TestConfigPaths:
    """Tests for path definitions."""

    def test_project_root_exists(self):
        """Verify that PROJECT_ROOT is a valid Path object."""
        assert isinstance(PROJECT_ROOT, Path), "PROJECT_ROOT must be a Path object"
        assert PROJECT_ROOT.exists(), "PROJECT_ROOT must exist on the filesystem"

    def test_data_dir_defined(self):
        """Verify that DATA_DIR is defined and under PROJECT_ROOT."""
        assert isinstance(DATA_DIR, Path), "DATA_DIR must be a Path object"
        assert DATA_DIR.is_absolute(), "DATA_DIR must be an absolute path"
        # DATA_DIR should be under PROJECT_ROOT
        assert DATA_DIR == PROJECT_ROOT / "data", "DATA_DIR should be PROJECT_ROOT/data"

    def test_metrics_csv_path_defined(self):
        """Verify that METRICS_CSV_PATH is defined."""
        assert isinstance(METRICS_CSV_PATH, Path), "METRICS_CSV_PATH must be a Path object"
        # Check that it ends with the expected filename
        assert METRICS_CSV_PATH.name == "metrics.csv", "METRICS_CSV_PATH should be named metrics.csv"


class TestDirectoryCreation:
    """Tests for directory creation functionality."""

    def test_ensure_directories_exist(self, tmp_path):
        """Test that ensure_directories_exist creates the required directories."""
        # Temporarily override PROJECT_ROOT and DATA_DIR for testing
        # We do this by mocking the module attributes or creating a custom test
        # For simplicity, we'll just ensure the function runs without error
        # and creates the directories it defines relative to the actual PROJECT_ROOT.
        # Since we can't easily mock the module-level constants in a simple test,
        # we rely on the fact that the function creates dirs under the real PROJECT_ROOT.
        
        # We'll check that the function doesn't crash and that key directories exist after call.
        # Note: This test might create dirs in the real project structure if run in a real env.
        # In a CI/test environment, this is usually acceptable as they are temporary or ignored.
        
        # To be safer, we can check that the function *would* create a specific subdirectory
        # by checking the logic, but the direct test is:
        try:
            ensure_directories_exist()
            # Verify that at least the main data directory exists
            assert DATA_DIR.exists(), "DATA_DIR should exist after calling ensure_directories_exist"
            assert DATA_DIR.is_dir(), "DATA_DIR should be a directory"
        except Exception as e:
            pytest.fail(f"ensure_directories_exist raised an exception: {e}")

    def test_subdirectories_created(self):
        """Test that specific subdirectories are created."""
        # Ensure directories exist first
        ensure_directories_exist()
        
        # Check a few key subdirectories
        assert (DATA_DIR / "raw").exists(), "data/raw should exist"
        assert (DATA_DIR / "processed").exists(), "data/processed should exist"
        assert (DATA_DIR / "stimuli").exists(), "data/stimuli should exist"
        assert (DATA_DIR / "measurements").exists(), "data/measurements should exist"
        assert (DATA_DIR / "derived").exists(), "data/derived should exist"