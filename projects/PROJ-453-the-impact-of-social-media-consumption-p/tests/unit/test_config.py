"""
Unit tests for code/config.py constants and functions.
"""

import pytest
import os
from pathlib import Path

try:
    from config import (
        RANDOM_SEED,
        DATA_ROOT,
        RESULTS_ROOT,
        ensure_directories,
        DATA_RAW,
        DATA_PROCESSED
    )
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
    from config import (
        RANDOM_SEED,
        DATA_ROOT,
        RESULTS_ROOT,
        ensure_directories,
        DATA_RAW,
        DATA_PROCESSED
    )


class TestConstants:
    """Tests for configuration constants."""

    def test_random_seed_is_integer(self):
        """Test that RANDOM_SEED is an integer."""
        assert isinstance(RANDOM_SEED, int)

    def test_random_seed_value(self):
        """Test that RANDOM_SEED is 42."""
        assert RANDOM_SEED == 42

    def test_data_root_is_string(self):
        """Test that DATA_ROOT is a string."""
        assert isinstance(DATA_ROOT, str)
        assert DATA_ROOT == "data"

    def test_results_root_is_string(self):
        """Test that RESULTS_ROOT is a string."""
        assert isinstance(RESULTS_ROOT, str)
        assert RESULTS_ROOT == "results"


class TestEnsureDirectories:
    """Tests for the ensure_directories function."""

    def test_creates_directories(self, tmp_path):
        """Test that ensure_directories creates the required folders."""
        # Change to tmp_path to avoid creating dirs in actual project
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            created_dirs = ensure_directories()

            # Check that we got a list
            assert isinstance(created_dirs, list)
            assert len(created_dirs) > 0

            # Check that directories actually exist
            for dir_path in created_dirs:
                assert dir_path.exists()
                assert dir_path.is_dir()
        finally:
            os.chdir(original_cwd)

    def test_directories_match_expected_names(self, tmp_path):
        """Test that created directories have expected names."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            ensure_directories()

            # Check specific expected directories
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "processed").exists()
            assert (tmp_path / "results" / "models").exists()
            assert (tmp_path / "results" / "figures").exists()
            assert (tmp_path / "logs").exists()
            assert (tmp_path / "contracts").exists()
        finally:
            os.chdir(original_cwd)