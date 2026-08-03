"""
Unit tests for frequentist aggregation models.
"""

import sys
import os
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.frequentist import simple_average, weighted_average


class TestSimpleAverage:
    """Tests for the simple_average function."""

    def test_basic_arithmetic_mean(self):
        """Test that simple average calculates the correct arithmetic mean."""
        data = pd.DataFrame({
            'week_start': ['2020-10-01', '2020-10-01', '2020-10-01', '2020-10-08'],
            'vote_share': [40.0, 50.0, 60.0, 70.0]
        })

        result = simple_average(data)

        # First week: (40+50+60)/3 = 50.0
        # Second week: 70.0
        expected = pd.DataFrame({
            'week_start': ['2020-10-01', '2020-10-08'],
            'simple_avg_forecast': [50.0, 70.0]
        })

        pd.testing.assert_frame_equal(result, expected)

    def test_single_poll_per_bin(self):
        """Test behavior when there is only one poll per week."""
        data = pd.DataFrame({
            'week_start': ['2020-10-01', '2020-10-08'],
            'vote_share': [45.0, 55.0]
        })

        result = simple_average(data)

        expected = pd.DataFrame({
            'week_start': ['2020-10-01', '2020-10-08'],
            'simple_avg_forecast': [45.0, 55.0]
        })

        pd.testing.assert_frame_equal(result, expected)

    def test_missing_columns(self):
        """Test that missing required columns raise an error."""
        data = pd.DataFrame({
            'week_start': ['2020-10-01'],
            # Missing vote_share
        })

        with pytest.raises(ValueError, match="Missing required column: vote_share"):
            simple_average(data)

    def test_empty_dataframe(self):
        """Test handling of empty input."""
        data = pd.DataFrame(columns=['week_start', 'vote_share'])

        result = simple_average(data)

        assert result.empty
        assert 'simple_avg_forecast' in result.columns
        assert 'week_start' in result.columns


class TestWeightedAverage:
    """Tests for the weighted_average function."""

    def test_inverse_rmse_normalization(self):
        """Test that weights are normalized correctly (inverse RMSE)."""
        # Two polls in same week:
        # Poll A: vote=40, rmse=1.0 -> inv=1.0
        # Poll B: vote=60, rmse=1.0 -> inv=1.0
        # Weights: 0.5, 0.5 -> Avg = 50.0
        data = pd.DataFrame({
            'week_start': ['2020-10-01', '2020-10-01'],
            'vote_share': [40.0, 60.0],
            'historical_rmse': [1.0, 1.0]
        })

        result = weighted_average(data)

        expected = pd.DataFrame({
            'week_start': ['2020-10-01'],
            'weighted_avg_forecast': [50.0]
        })

        pd.testing.assert_frame_equal(result, expected)

    def test_different_rmse_weights(self):
        """Test weighted average with different RMSE values."""
        # Poll A: vote=40, rmse=2.0 -> inv=0.5
        # Poll B: vote=60, rmse=1.0 -> inv=1.0
        # Total inv = 1.5
        # Weight A = 0.5/1.5 = 1/3
        # Weight B = 1.0/1.5 = 2/3
        # Avg = 40*(1/3) + 60*(2/3) = 13.33 + 40 = 53.33
        data = pd.DataFrame({
            'week_start': ['2020-10-01', '2020-10-01'],
            'vote_share': [40.0, 60.0],
            'historical_rmse': [2.0, 1.0]
        })

        result = weighted_average(data)

        expected_val = 40.0 * (1/3) + 60.0 * (2/3)

        assert abs(result['weighted_avg_forecast'].iloc[0] - expected_val) < 1e-6

    def test_missing_weights_column(self):
        """Test that missing weights column raises an error."""
        data = pd.DataFrame({
            'week_start': ['2020-10-01'],
            'vote_share': [50.0]
            # Missing historical_rmse
        })

        with pytest.raises(ValueError, match="Missing required column: historical_rmse"):
            weighted_average(data)

    def test_non_positive_weights_filtered(self):
        """Test that non-positive RMSE values are filtered out."""
        data = pd.DataFrame({
            'week_start': ['2020-10-01', '2020-10-01', '2020-10-01'],
            'vote_share': [40.0, 50.0, 60.0],
            'historical_rmse': [1.0, 0.0, 2.0]  # 0.0 should be excluded
        })

        # Should use only the rows with rmse=1.0 and rmse=2.0
        result = weighted_average(data)

        # Poll A (40, rmse=1) and Poll C (60, rmse=2)
        # inv_A = 1, inv_C = 0.5, total = 1.5
        # w_A = 2/3, w_C = 1/3
        # avg = 40*(2/3) + 60*(1/3) = 26.67 + 20 = 46.67
        expected_val = 40.0 * (2/3) + 60.0 * (1/3)

        assert abs(result['weighted_avg_forecast'].iloc[0] - expected_val) < 1e-6

    def test_empty_after_filtering(self):
        """Test behavior when all weights are non-positive."""
        data = pd.DataFrame({
            'week_start': ['2020-10-01'],
            'vote_share': [50.0],
            'historical_rmse': [0.0]
        })

        result = weighted_average(data)

        assert result.empty
        assert 'weighted_avg_forecast' in result.columns
        assert 'week_start' in result.columns