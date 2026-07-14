"""
Unit tests for the configuration module (code/config.py).

Tests verify that paths are constructed correctly, thresholds are set as expected,
and helper functions work properly.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import (
    PROJECT_ROOT,
    DATA_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    RANDOM_SEED,
    PREVALENCE_THRESHOLD,
    RAREFACTION_LOSS_THRESHOLD,
    MIN_SEQUENCING_DEPTH,
    PHQ9_HIGH_THRESHOLD,
    GAD7_HIGH_THRESHOLD,
    ALPHA_FDR,
    AGP_STUDY_ID,
    ensure_directories,
    get_output_path,
    calculate_median_depth,
    estimate_rarefaction_loss,
    set_random_seed,
    CONFIG
)

import numpy as np


class TestConfigurationValues:
    """Test that configuration constants are set correctly."""

    def test_random_seed_is_set(self):
        assert RANDOM_SEED == 42

    def test_prevalence_threshold(self):
        assert PREVALENCE_THRESHOLD == 0.001  # 0.1%

    def test_rarefaction_loss_threshold(self):
        assert RAREFACTION_LOSS_THRESHOLD == 0.20  # 20%

    def test_min_sequencing_depth(self):
        assert MIN_SEQUENCING_DEPTH == 1000

    def test_phq9_high_threshold(self):
        assert PHQ9_HIGH_THRESHOLD == 10

    def test_gad7_high_threshold(self):
        assert GAD7_HIGH_THRESHOLD == 10

    def test_alpha_fdr(self):
        assert ALPHA_FDR == 0.05

    def test_agp_study_id(self):
        assert AGP_STUDY_ID == "10317"

    def test_config_dict_structure(self):
        assert "paths" in CONFIG
        assert "random_seed" in CONFIG
        assert "thresholds" in CONFIG
        assert "analysis" in CONFIG
        assert "api" in CONFIG


class TestPathConfiguration:
    """Test path construction and directory handling."""

    def test_project_root_is_absolute(self):
        assert PROJECT_ROOT.is_absolute()

    def test_data_dir_exists_or_is_parent(self):
        # The directory might not exist yet, but the path object should be valid
        assert isinstance(DATA_DIR, Path)
        assert DATA_DIR.name == "data"

    def test_get_output_path_processed(self):
        path = get_output_path("test.csv", "processed")
        assert path.parent == PROCESSED_DATA_DIR
        assert path.name == "test.csv"

    def test_get_output_path_raw(self):
        path = get_output_path("raw_data.csv", "raw")
        assert path.parent == RAW_DATA_DIR
        assert path.name == "raw_data.csv"

    def test_get_output_path_plots(self):
        path = get_output_path("plot.png", "plots")
        assert "results" in str(path.parent)
        assert "plots" in str(path)

    def test_get_output_path_default(self):
        # Default should be processed
        path = get_output_path("default.csv")
        assert path.parent == PROCESSED_DATA_DIR

    @patch('code.config.Path.mkdir')
    def test_ensure_directories_creates_dirs(self, mock_mkdir):
        """Test that ensure_directories attempts to create all necessary directories."""
        ensure_directories()
        # Check that mkdir was called multiple times
        assert mock_mkdir.call_count > 0


class TestHelperFunctions:
    """Test utility functions defined in config.py."""

    def test_calculate_median_depth_basic(self):
        """Test median depth calculation with simple data."""
        # 3 samples, depths: 100, 200, 300 -> median 200
        counts = np.array([
            [10, 0, 0],  # sum 10
            [0, 20, 0],  # sum 20
            [0, 0, 30],  # sum 30
        ])
        median = calculate_median_depth(counts)
        assert median == 20.0

    def test_calculate_median_depth_with_zeros(self):
        """Test median depth calculation ignoring zero-depth samples."""
        counts = np.array([
            [0, 0, 0],  # sum 0 (should be ignored)
            [0, 20, 0],  # sum 20
            [0, 0, 30],  # sum 30
        ])
        median = calculate_median_depth(counts)
        assert median == 25.0  # median of [20, 30]

    def test_calculate_median_depth_empty(self):
        """Test median depth with all zeros."""
        counts = np.array([
            [0, 0, 0],
            [0, 0, 0],
        ])
        median = calculate_median_depth(counts)
        assert median == 0.0

    def test_estimate_rarefaction_loss_partial(self):
        """Test loss estimation when some samples are below threshold."""
        depths = [100, 200, 300, 400]
        target = 250
        # 2 samples (100, 200) are below 250 -> 50% loss
        loss = estimate_rarefaction_loss(depths, target)
        assert loss == 0.5

    def test_estimate_rarefaction_loss_all_good(self):
        """Test loss estimation when all samples are above threshold."""
        depths = [300, 400, 500]
        target = 200
        loss = estimate_rarefaction_loss(depths, target)
        assert loss == 0.0

    def test_estimate_rarefaction_loss_all_bad(self):
        """Test loss estimation when all samples are below threshold."""
        depths = [100, 200, 300]
        target = 400
        loss = estimate_rarefaction_loss(depths, target)
        assert loss == 1.0

    def test_estimate_rarefaction_loss_empty(self):
        """Test loss estimation with empty list."""
        loss = estimate_rarefaction_loss([], 100)
        assert loss == 1.0


class TestRandomSeedSetting:
    """Test that random seed setting functions work."""

    def test_set_random_seed_runs_without_error(self):
        """Test that set_random_seed executes without raising exceptions."""
        # Should not raise
        set_random_seed(123)

    def test_set_random_seed_sets_numpy(self):
        """Test that numpy seed is set correctly."""
        set_random_seed(42)
        try:
            import numpy as np
            a = np.random.rand()
            set_random_seed(42)
            b = np.random.rand()
            assert a == b, "Numpy random state should be reproducible"
        except ImportError:
            pytest.skip("NumPy not installed")

    def test_set_random_seed_sets_python_builtin(self):
        """Test that Python's random module seed is set."""
        import random
        set_random_seed(42)
        a = random.random()
        set_random_seed(42)
        b = random.random()
        assert a == b, "Python random state should be reproducible"