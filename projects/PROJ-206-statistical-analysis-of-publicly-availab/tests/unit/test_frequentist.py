"""
Unit tests for frequentist aggregation methods in src/models/frequentist.py.
Verifies edge cases including single poll inputs, missing weights, and zero-division handling.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure src is in path for imports during test execution
root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root / "code"))

from src.models.frequentist import simple_average, weighted_average


class TestSimpleAverage:
    """Tests for the simple_average function."""

    def test_single_poll(self):
        """Edge case: Input contains exactly one poll."""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2024-10-01']),
            'vote_share': [45.5],
            'pollster': ['PollA']
        })
        result = simple_average(data)
        assert isinstance(result, pd.DataFrame)
        assert 'simple_avg_forecast' in result.columns
        assert result['simple_avg_forecast'].iloc[0] == 45.5

    def test_multiple_polls_same_bin(self):
        """Standard case: Multiple polls in the same weekly bin."""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2024-10-01', '2024-10-02', '2024-10-03']),
            'vote_share': [40.0, 50.0, 60.0],
            'pollster': ['PollA', 'PollB', 'PollC']
        })
        result = simple_average(data)
        assert result['simple_avg_forecast'].iloc[0] == 50.0

    def test_empty_dataframe(self):
        """Edge case: Empty input dataframe."""
        data = pd.DataFrame(columns=['date', 'vote_share', 'pollster'])
        data['date'] = pd.to_datetime(data['date'])
        result = simple_average(data)
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_missing_vote_share_values(self):
        """Edge case: Some vote_share values are NaN."""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2024-10-01', '2024-10-02']),
            'vote_share': [40.0, np.nan],
            'pollster': ['PollA', 'PollB']
        })
        result = simple_average(data)
        # simple_average should handle NaN by ignoring them in mean calculation
        assert result['simple_avg_forecast'].iloc[0] == 40.0


class TestWeightedAverage:
    """Tests for the weighted_average function."""

    def test_single_poll_with_weight(self):
        """Edge case: Single poll with a valid weight."""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2024-10-01']),
            'vote_share': [45.5],
            'pollster': ['PollA'],
            'historical_rmse': [1.2]
        })
        result = weighted_average(data)
        assert isinstance(result, pd.DataFrame)
        assert 'weighted_avg_forecast' in result.columns
        # With one poll, the weighted average equals the vote share
        assert result['weighted_avg_forecast'].iloc[0] == 45.5

    def test_missing_weights(self):
        """Edge case: Some polls have missing (NaN) historical_rmse weights."""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2024-10-01', '2024-10-02']),
            'vote_share': [40.0, 50.0],
            'pollster': ['PollA', 'PollB'],
            'historical_rmse': [1.0, np.nan]
        })
        # Function should handle NaN weights, likely by dropping them or treating as 0
        # We expect it to not crash and return a result based on available valid weights
        result = weighted_average(data)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        # If one weight is NaN, it should be excluded from the weighted mean calculation
        # So the result should be the vote_share of the valid row
        assert result['weighted_avg_forecast'].iloc[0] == 40.0

    def test_zero_rmse_prevention(self):
        """Edge case: A poll has 0.0 historical_rmse (potential division by zero)."""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2024-10-01', '2024-10-02']),
            'vote_share': [40.0, 50.0],
            'pollster': ['PollA', 'PollB'],
            'historical_rmse': [0.0, 1.0]
        })
        # The implementation should handle 0.0 RMSE (e.g., by adding epsilon or capping)
        # to prevent division by zero. It should not raise an exception.
        result = weighted_average(data)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_normalization(self):
        """Verify that weights sum to 1.0 in the calculation."""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2024-10-01', '2024-10-02']),
            'vote_share': [40.0, 60.0],
            'pollster': ['PollA', 'PollB'],
            'historical_rmse': [2.0, 1.0]
        })
        # Inverse RMSE: 1/2 = 0.5, 1/1 = 1.0. Sum = 1.5.
        # Normalized weights: 0.5/1.5 = 1/3, 1.0/1.5 = 2/3.
        # Expected forecast: (40 * 1/3) + (60 * 2/3) = 13.33 + 40 = 53.33
        expected = (40.0 * (1/3)) + (60.0 * (2/3))
        result = weighted_average(data)
        np.testing.assert_almost_equal(result['weighted_avg_forecast'].iloc[0], expected, decimal=5)

    def test_empty_dataframe(self):
        """Edge case: Empty input dataframe."""
        data = pd.DataFrame(columns=['date', 'vote_share', 'pollster', 'historical_rmse'])
        data['date'] = pd.to_datetime(data['date'])
        result = weighted_average(data)
        assert isinstance(result, pd.DataFrame)
        assert result.empty