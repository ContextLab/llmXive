"""
Unit tests for code/utils/config.py.
Verifies config loading, path resolution, and seed reproducibility.
"""

import os
import random
import numpy as np
import pytest
from pathlib import Path

# Import the config module using the relative path structure expected in the project
# Assuming tests/ is at the root level alongside code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.config import (
    PROJECT_ROOT,
    DATA_DIR,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    CODE_DIR,
    TESTS_DIR,
    LOGS_DIR,
    FIGURES_DIR,
    RESULTS_DIR,
    RESULTS_DIAGNOSTICS_DIR,
    SPEC_DIR,
    RANDOM_SEED,
    VIF_THRESHOLD,
    SENTIMENT_RANGE,
    MISSING_SENTINEL,
    load_config,
    set_seed,
    get_config_summary
)


class TestConfigPaths:
    """Test that all path constants are correctly resolved."""

    def test_project_root_exists(self):
        """PROJECT_ROOT should be a valid Path object pointing to the repo root."""
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.exists()

    def test_data_dirs_exist_or_are_parent_of_existing(self):
        """Data directories should resolve to valid paths under the project root."""
        assert isinstance(DATA_DIR, Path)
        assert str(DATA_DIR).startswith(str(PROJECT_ROOT))
        
        # Raw and processed dirs should be under DATA_DIR
        assert DATA_RAW_DIR.parent == DATA_DIR
        assert DATA_PROCESSED_DIR.parent == DATA_DIR

    def test_code_and_tests_dirs(self):
        """Code and tests directories should resolve correctly."""
        assert isinstance(CODE_DIR, Path)
        assert isinstance(TESTS_DIR, Path)
        assert str(CODE_DIR).startswith(str(PROJECT_ROOT))
        assert str(TESTS_DIR).startswith(str(PROJECT_ROOT))

    def test_logs_dir(self):
        """Logs directory should be a valid path."""
        assert isinstance(LOGS_DIR, Path)
        assert str(LOGS_DIR).startswith(str(PROJECT_ROOT))

    def test_figures_and_results_dirs(self):
        """Figures and Results directories should be valid paths."""
        assert isinstance(FIGURES_DIR, Path)
        assert isinstance(RESULTS_DIR, Path)
        assert str(FIGURES_DIR).startswith(str(PROJECT_ROOT))
        assert str(RESULTS_DIR).startswith(str(PROJECT_ROOT))

    def test_diagnostics_subdir(self):
        """Diagnostics directory should be a subdirectory of RESULTS_DIR."""
        assert RESULTS_DIAGNOSTICS_DIR.parent == RESULTS_DIR


class TestConfigValues:
    """Test that configuration values match expectations."""

    def test_random_seed_is_integer(self):
        """RANDOM_SEED must be an integer."""
        assert isinstance(RANDOM_SEED, int)

    def test_vif_threshold_is_float(self):
        """VIF_THRESHOLD must be a positive float."""
        assert isinstance(VIF_THRESHOLD, float)
        assert VIF_THRESHOLD > 0

    def test_sentiment_range_format(self):
        """SENTIMENT_RANGE must be a tuple/list of two floats."""
        assert isinstance(SENTIMENT_RANGE, (tuple, list))
        assert len(SENTIMENT_RANGE) == 2
        assert isinstance(SENTIMENT_RANGE[0], float)
        assert isinstance(SENTIMENT_RANGE[1], float)
        # Typically [-1.0, 1.0]
        assert SENTIMENT_RANGE[0] <= SENTIMENT_RANGE[1]

    def test_missing_sentinel(self):
        """MISSING_SENTINEL must be a numeric value (typically -999.0)."""
        assert isinstance(MISSING_SENTINEL, (int, float))


class TestSeedReproducibility:
    """Test that set_seed ensures reproducibility."""

    def test_set_seed_reproducibility_python(self):
        """Verify that random module produces same sequence after set_seed."""
        set_seed(RANDOM_SEED)
        seq1 = [random.random() for _ in range(5)]

        set_seed(RANDOM_SEED)
        seq2 = [random.random() for _ in range(5)]

        assert seq1 == seq2

    def test_set_seed_reproducibility_numpy(self):
        """Verify that numpy produces same sequence after set_seed."""
        set_seed(RANDOM_SEED)
        arr1 = np.random.rand(5)

        set_seed(RANDOM_SEED)
        arr2 = np.random.rand(5)

        np.testing.assert_array_equal(arr1, arr2)

    def test_set_seed_different_seeds_different_results(self):
        """Verify that different seeds produce different results."""
        set_seed(42)
        arr1 = np.random.rand(5)

        set_seed(123)
        arr2 = np.random.rand(5)

        assert not np.array_equal(arr1, arr2)


class TestLoadConfig:
    """Test the load_config function."""

    def test_load_config_returns_dict(self):
        """load_config should return a dictionary."""
        config = load_config()
        assert isinstance(config, dict)

    def test_load_config_contains_expected_keys(self):
        """load_config should contain expected configuration keys."""
        config = load_config()
        expected_keys = [
            "project_root", "data_dir", "data_raw_dir", "data_processed_dir",
            "code_dir", "tests_dir", "logs_dir", "figures_dir", "results_dir",
            "random_seed", "vif_threshold", "sentiment_range", "missing_sentinel"
        ]
        for key in expected_keys:
            assert key in config

    def test_load_config_values_match_constants(self):
        """Values returned by load_config should match module constants."""
        config = load_config()
        assert config["random_seed"] == RANDOM_SEED
        assert config["vif_threshold"] == VIF_THRESHOLD
        assert config["missing_sentinel"] == MISSING_SENTINEL


class TestGetConfigSummary:
    """Test the get_config_summary function."""

    def test_get_config_summary_returns_string(self):
        """get_config_summary should return a string."""
        summary = get_config_summary()
        assert isinstance(summary, str)

    def test_get_config_summary_contains_seed(self):
        """Summary should contain the random seed value."""
        summary = get_config_summary()
        assert str(RANDOM_SEED) in summary

    def test_get_config_summary_contains_paths(self):
        """Summary should contain key directory paths."""
        summary = get_config_summary()
        assert "project_root" in summary.lower() or str(PROJECT_ROOT) in summary