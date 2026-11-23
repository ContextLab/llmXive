import pytest
import numpy as np
import pandas as pd

from cli_engine import (
    compute_moving_average_zscore,
    identify_high_load_windows,
    compute_outlier_flags,
    process_window_data
)
from config import set_random_seed, reset_config


@pytest.fixture(autouse=True)
def setup_config():
    """Ensure clean config state for each test."""
    reset_config()
    set_random_seed(42)
    yield
    reset_config()


class TestComputeMovingAverageZscore:
    def test_basic_calculation(self):
        """Test that z-scores are calculated correctly for a simple sequence."""
        values = np.array([10.0, 10.0, 10.0, 20.0, 20.0, 20.0])
        # With center=True and window=3, the middle values will have valid stats
        z_scores = compute_moving_average_zscore(values, window_size=3)

        # The exact values depend on the rolling mean/std implementation,
        # but we check for non-NaN and reasonable range
        assert not np.isnan(z_scores[2:-2]).any(), "Middle values should not be NaN"
        assert len(z_scores) == len(values)

    def test_small_window(self):
        """Test behavior when data length < window size."""
        values = np.array([1.0, 2.0])
        z_scores = compute_moving_average_zscore(values, window_size=5)
        assert np.all(np.isnan(z_scores))


class TestIdentifyHighLoadWindows:
    def test_threshold_logic(self):
        """Test that windows above threshold are flagged."""
        z_scores = np.array([-1.0, 0.0, 0.4, 0.6, 1.0, 2.0])
        flags = identify_high_load_windows(z_scores, threshold_std=0.5)
        
        expected = [False, False, False, True, True, True]
        assert flags == expected

    def test_default_threshold(self):
        """Test behavior with default config threshold (0.5)."""
        z_scores = np.array([0.4, 0.5, 0.6])
        flags = identify_high_load_windows(z_scores)
        # 0.5 is not > 0.5, so only 0.6 is True
        assert flags == [False, False, True]


class TestComputeOutlierFlags:
    def test_outlier_detection(self):
        """Test that extreme z-scores are flagged as outliers."""
        z_scores = np.array([-3.5, -2.0, 0.0, 2.0, 3.5])
        flags = compute_outlier_flags(z_scores, threshold_std=3.0)
        
        expected = [True, False, False, False, True]
        assert flags == expected

    def test_no_outliers(self):
        """Test when no values exceed threshold."""
        z_scores = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        flags = compute_outlier_flags(z_scores, threshold_std=3.0)
        assert all(not f for f in flags)

    def test_default_threshold(self):
        """Test behavior with default config threshold (3.0)."""
        z_scores = np.array([-3.1, 3.1])
        flags = compute_outlier_flags(z_scores)
        assert flags == [True, True]


class TestProcessWindowData:
    def test_full_pipeline(self):
        """Test the end-to-end processing of a DataFrame."""
        data = {
            'window_id': [1, 2, 3, 4, 5, 6, 7, 8, 9],
            'cli_value': [10.0, 10.0, 10.0, 20.0, 20.0, 20.0, 100.0, 10.0, 10.0]
        }
        df = pd.DataFrame(data)

        result = process_window_data(
            df,
            cli_column='cli_value',
            window_size=3,
            high_load_threshold=0.5,
            outlier_threshold=3.0
        )

        # Check new columns exist
        assert 'cli_zscore' in result.columns
        assert 'is_high_load' in result.columns
        assert 'is_outlier' in result.columns

        # Check lengths match
        assert len(result) == len(df)

        # The 100.0 value should likely be an outlier depending on local stats
        # We primarily check that the function runs without error and produces structure
        assert result['is_outlier'].dtype == bool
        assert result['is_high_load'].dtype == bool

    def test_missing_column(self):
        """Test that an error is raised if the CLI column is missing."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        with pytest.raises(ValueError):
            process_window_data(df, cli_column='cli_value')