"""
Unit tests for src/models/frequentist.py
Verifying edge cases: single poll, missing weights, empty input, etc.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import os

# Ensure src is in path
src_path = Path(__file__).parent.parent.parent / "code" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.models.frequentist import simple_average, weighted_average


class TestSimpleAverage:
    """Tests for the simple_average function."""

    def test_single_poll(self):
        """Edge case: Single poll should return that poll's vote share."""
        data = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-01')],
            'pollster': ['Poll A'],
            'vote_share': [52.5],
            'sample_size': [1000],
            'historical_rmse': [2.0],
            'week_bin': ['2024-W01']
        })

        result = simple_average(data)

        assert len(result) == 1
        assert result.iloc[0]['simple_avg_forecast'] == 52.5
        assert result.iloc[0]['week_bin'] == '2024-W01'

    def test_multiple_polls_same_week(self):
        """Standard case: Multiple polls in same week should average correctly."""
        data = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-02'), pd.Timestamp('2024-01-03')],
            'pollster': ['Poll A', 'Poll B'],
            'vote_share': [50.0, 60.0],
            'sample_size': [1000, 1000],
            'historical_rmse': [2.0, 2.0],
            'week_bin': ['2024-W01', '2024-W01']
        })

        result = simple_average(data)

        assert len(result) == 1
        # (50 + 60) / 2 = 55.0
        assert np.isclose(result.iloc[0]['simple_avg_forecast'], 55.0)

    def test_empty_dataframe(self):
        """Edge case: Empty input should return empty output."""
        data = pd.DataFrame(columns=['date', 'pollster', 'vote_share', 'sample_size', 'historical_rmse', 'week_bin'])

        result = simple_average(data)

        assert len(result) == 0
        assert 'simple_avg_forecast' in result.columns

    def test_multiple_week_bins(self):
        """Standard case: Data spanning multiple weeks should be grouped correctly."""
        data = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-02'), pd.Timestamp('2024-01-10')],
            'pollster': ['Poll A', 'Poll B'],
            'vote_share': [50.0, 60.0],
            'sample_size': [1000, 1000],
            'historical_rmse': [2.0, 2.0],
            'week_bin': ['2024-W01', '2024-W02']
        })

        result = simple_average(data)

        assert len(result) == 2
        # Check values match source
        w1 = result[result['week_bin'] == '2024-W01'].iloc[0]
        w2 = result[result['week_bin'] == '2024-W02'].iloc[0]

        assert np.isclose(w1['simple_avg_forecast'], 50.0)
        assert np.isclose(w2['simple_avg_forecast'], 60.0)


class TestWeightedAverage:
    """Tests for the weighted_average function."""

    def test_single_poll(self):
        """Edge case: Single poll with weight should return that poll's vote share."""
        data = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-01')],
            'pollster': ['Poll A'],
            'vote_share': [52.5],
            'sample_size': [1000],
            'historical_rmse': [2.0],
            'week_bin': ['2024-W01']
        })

        result = weighted_average(data)

        assert len(result) == 1
        # Weight is 1/RMSE = 0.5. Normalized weight = 1.0.
        # Forecast = 52.5 * 1.0 = 52.5
        assert np.isclose(result.iloc[0]['weighted_avg_forecast'], 52.5)

    def test_missing_weights_zero_rmse_handling(self):
        """Edge case: Polls with RMSE=0 should be handled (avoid division by zero).
        
        Expected behavior: If RMSE is 0, the weight calculation (1/RMSE) would be infinite.
        The implementation should handle this by either:
        1. Assigning a very large weight (effectively dominating)
        2. Assigning a default high weight
        3. Skipping the poll
        
        Based on typical implementations, we test that the function doesn't crash
        and produces a valid float result.
        """
        data = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-02')],
            'pollster': ['Perfect Poll', 'Normal Poll'],
            'vote_share': [50.0, 60.0],
            'sample_size': [1000, 1000],
            'historical_rmse': [0.0, 2.0],  # One has 0 RMSE
            'week_bin': ['2024-W01', '2024-W01']
        })

        # This should not raise an exception
        result = weighted_average(data)

        assert len(result) == 1
        assert 'weighted_avg_forecast' in result.columns
        assert np.isfinite(result.iloc[0]['weighted_avg_forecast'])

    def test_multiple_polls_same_week(self):
        """Standard case: Multiple polls should be weighted by inverse RMSE."""
        # Poll A: RMSE=2.0 -> weight = 0.5
        # Poll B: RMSE=1.0 -> weight = 1.0
        # Total weight = 1.5
        # Normalized: A = 0.5/1.5 = 1/3, B = 1.0/1.5 = 2/3
        # Forecast = 50*(1/3) + 60*(2/3) = 16.67 + 40 = 56.67
        data = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-02'), pd.Timestamp('2024-01-03')],
            'pollster': ['Poll A', 'Poll B'],
            'vote_share': [50.0, 60.0],
            'sample_size': [1000, 1000],
            'historical_rmse': [2.0, 1.0],
            'week_bin': ['2024-W01', '2024-W01']
        })

        result = weighted_average(data)

        assert len(result) == 1
        expected = 50.0 * (1/3) + 60.0 * (2/3)
        assert np.isclose(result.iloc[0]['weighted_avg_forecast'], expected, rtol=1e-4)

    def test_empty_dataframe(self):
        """Edge case: Empty input should return empty output."""
        data = pd.DataFrame(columns=['date', 'pollster', 'vote_share', 'sample_size', 'historical_rmse', 'week_bin'])

        result = weighted_average(data)

        assert len(result) == 0
        assert 'weighted_avg_forecast' in result.columns

    def test_missing_weights_default_handling(self):
        """Edge case: Missing historical_rmse (NaN) should be handled gracefully.
        
        Expected behavior: The function should either:
        1. Filter out rows with NaN RMSE
        2. Assign a default median weight
        
        We test that the function completes without crashing.
        """
        data = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-02')],
            'pollster': ['New Poll', 'Known Poll'],
            'vote_share': [50.0, 60.0],
            'sample_size': [1000, 1000],
            'historical_rmse': [np.nan, 2.0],
            'week_bin': ['2024-W01', '2024-W01']
        })

        # Should not crash
        result = weighted_average(data)

        assert len(result) >= 0  # Could be 0 if all filtered, or 1 if one remains
        assert 'weighted_avg_forecast' in result.columns
        if len(result) > 0:
            assert np.isfinite(result.iloc[0]['weighted_avg_forecast'])

    def test_all_nan_weights(self):
        """Edge case: All RMSE values are NaN. Should handle without crashing."""
        data = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-02')],
            'pollster': ['New Poll 1', 'New Poll 2'],
            'vote_share': [50.0, 60.0],
            'sample_size': [1000, 1000],
            'historical_rmse': [np.nan, np.nan],
            'week_bin': ['2024-W01', '2024-W01']
        })

        result = weighted_average(data)

        assert len(result) == 1
        assert np.isfinite(result.iloc[0]['weighted_avg_forecast'])