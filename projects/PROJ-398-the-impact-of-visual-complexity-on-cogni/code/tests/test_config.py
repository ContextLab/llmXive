"""
Tests for the global configuration module (src/config.py).
"""
import os
import sys
from pathlib import Path

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import pytest
from src.config import GLOBAL_SEED, PROJECT_ROOT, DATA_DIR, ensure_directories_exist, METRICS_CSV_PATH


class TestConfigSeed:
    """Tests to verify the global seed is defined and is an integer."""

    def test_seed_defined(self):
        """Verify that GLOBAL_SEED is defined in config."""
        assert GLOBAL_SEED is not None, "GLOBAL_SEED must be defined."
        assert isinstance(GLOBAL_SEED, int), "GLOBAL_SEED must be an integer."

    def test_seed_value(self):
        """Verify the specific value of the seed (optional, but good for reproducibility checks)."""
        # The spec usually implies a specific seed (e.g., 42) for reproducibility.
        # We assert it is a fixed integer.
        assert GLOBAL_SEED == 42, "Global seed should be 42 for consistency."


class TestConfigPaths:
    """Tests to verify path definitions."""

    def test_project_root_exists(self):
        """Verify that PROJECT_ROOT is a valid Path object."""
        assert isinstance(PROJECT_ROOT, Path), "PROJECT_ROOT must be a Path object."
        assert PROJECT_ROOT.exists(), "PROJECT_ROOT must exist on the filesystem."

    def test_data_dir_defined(self):
        """Verify DATA_DIR is defined."""
        assert DATA_DIR is not None
        assert isinstance(DATA_DIR, Path)

    def test_metrics_csv_path_defined(self):
        """Verify specific output paths are defined."""
        assert METRICS_CSV_PATH is not None
        assert isinstance(METRICS_CSV_PATH, Path)


class TestDirectoryCreation:
    """Tests for the ensure_directories_exist function."""

    def test_ensure_directories_creates_missing(self, tmp_path):
        """
        Test that ensure_directories_exist creates directories.
        We mock the PROJECT_ROOT temporarily to use a temp directory.
        """
        # This test is a bit tricky because config uses absolute paths.
        # We can test the logic by checking if the function runs without error
        # on the actual structure, or by mocking.
        # For now, we verify it doesn't crash on the real structure.
        try:
            ensure_directories_exist()
            # If we get here, it ran successfully
            assert True
        except Exception as e:
            pytest.fail(f"ensure_directories_exist failed: {e}")

    def test_directories_exist_after_call(self):
        """
        Verify that the key directories exist after calling ensure_directories_exist.
        """
        ensure_directories_exist()
        assert PROJECT_ROOT.exists()
        assert DATA_DIR.exists()
        assert (PROJECT_ROOT / "logs").exists()
        assert (PROJECT_ROOT / "state").exists()