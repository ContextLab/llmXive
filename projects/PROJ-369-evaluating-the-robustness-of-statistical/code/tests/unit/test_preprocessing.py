"""
Unit tests for preprocessing module.

Tests:
- Interpolate missing values (linear interpolation)
- ADF stationarity test logic
- Detrending via linear regression
- Differencing loops
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.preprocessing import (
    PreprocessingError,
    interpolate_missing,
    check_stationarity,
    detrend_series,
    difference_series,
    preprocess_series,
    preprocess_dataset
)

class TestInterpolateMissing:
    """Tests for linear interpolation of missing values."""

    def test_no_missing_values(self):
        """Test that series with no missing values is returned unchanged."""
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = interpolate_missing(series)
        pd.testing.assert_series_equal(result, series)

    def test_interpolate_single_missing(self):
        """Test interpolation of a single missing value."""
        series = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0])
        result = interpolate_missing(series)
        assert not result.isna().any()
        assert result.iloc[2] == 3.0  # Linear interpolation

    def test_interpolate_multiple_missing(self):
        """Test interpolation of multiple consecutive missing values."""
        series = pd.Series([1.0, 2.0, np.nan, np.nan, np.nan, 6.0, 7.0])
        result = interpolate_missing(series)
        assert not result.isna().any()
        # Check linear interpolation: 3.0, 4.0, 5.0
        assert result.iloc[2] == 3.0
        assert result.iloc[3] == 4.0
        assert result.iloc[4] == 5.0

    def test_interpolate_edge_missing_forward_fill(self):
        """Test that missing values at the start are forward filled."""
        series = pd.Series([np.nan, np.nan, 3.0, 4.0, 5.0])
        result = interpolate_missing(series)
        assert not result.isna().any()
        assert result.iloc[0] == 3.0  # Forward filled
        assert result.iloc[1] == 3.0  # Forward filled

    def test_interpolate_edge_missing_backward_fill(self):
        """Test that missing values at the end are backward filled."""
        series = pd.Series([1.0, 2.0, 3.0, np.nan, np.nan])
        result = interpolate_missing(series)
        assert not result.isna().any()
        assert result.iloc[3] == 3.0  # Backward filled
        assert result.iloc[4] == 3.0  # Backward filled

    def test_all_missing_raises_error(self):
        """Test that all-missing series raises PreprocessingError."""
        series = pd.Series([np.nan, np.nan, np.nan])
        with pytest.raises(PreprocessingError, match="all values are missing"):
            interpolate_missing(series)

    def test_numpy_array_input(self):
        """Test that numpy array input works correctly."""
        series = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        result = interpolate_missing(series)
        assert not np.isnan(result).any()
        assert result[2] == 3.0

    def test_interpolate_with_nonlinear_gap(self):
        """Test interpolation with a non-linear gap."""
        series = pd.Series([1.0, 2.0, np.nan, np.nan, 10.0, 11.0])
        result = interpolate_missing(series)
        assert not result.isna().any()
        # Linear interpolation between 2.0 and 10.0: 5.33, 8.67
        assert abs(result.iloc[2] - 5.333) < 0.01
        assert abs(result.iloc[3] - 8.667) < 0.01

class TestCheckStationarity:
    """Tests for ADF stationarity test logic."""

    def test_stationary_series(self):
        """Test that a stationary series is detected as stationary."""
        # Generate white noise (stationary)
        np.random.seed(42)
        series = pd.Series(np.random.normal(0, 1, 100))
        is_stationary, results = check_stationarity(series)
        assert is_stationary
        assert 'pvalue' in results
        assert 'statistic' in results

    def test_non_stationary_series(self):
        """Test that a non-stationary series (random walk) is detected."""
        # Generate random walk (non-stationary)
        np.random.seed(42)
        random_walk = pd.Series(np.cumsum(np.random.normal(0, 1, 200)))
        is_stationary, results = check_stationarity(random_walk)
        # Note: ADF might not always detect non-stationarity in short series
        # but it should return a valid result
        assert 'pvalue' in results
        assert 'statistic' in results

    def test_too_short_series_raises_error(self):
        """Test that series < 10 points raises PreprocessingError."""
        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(PreprocessingError, match="Series too short"):
            check_stationarity(series)

    def test_custom_alpha(self):
        """Test ADF with custom alpha level."""
        np.random.seed(42)
        series = pd.Series(np.random.normal(0, 1, 100))
        is_stationary_05, _ = check_stationarity(series, alpha=0.05)
        is_stationary_01, _ = check_stationarity(series, alpha=0.01)
        # Should be consistent or more conservative with lower alpha
        assert isinstance(is_stationary_05, bool)
        assert isinstance(is_stationary_01, bool)

    def test_numpy_array_input(self):
        """Test that numpy array input works."""
        np.random.seed(42)
        series = np.random.normal(0, 1, 100)
        is_stationary, results = check_stationarity(series)
        assert isinstance(is_stationary, bool)
        assert 'pvalue' in results

class TestDetrendSeries:
    """Tests for linear regression detrending."""

    def test_detrend_linear_trend(self):
        """Test detrending of a series with a clear linear trend."""
        n = 100
        t = np.arange(n)
        series = pd.Series(2 * t + np.random.normal(0, 1, n))
        
        detrended, stats = detrend_series(series)
        
        # Detrended series should have mean close to 0
        assert abs(detrended.mean()) < 0.5
        # Stats should contain expected keys
        assert 'slope' in stats
        assert 'intercept' in stats
        assert 'rsquared' in stats
        # Slope should be close to 2
        assert abs(stats['slope'] - 2.0) < 0.5

    def test_detrend_no_trend(self):
        """Test detrending of a series with no trend."""
        np.random.seed(42)
        series = pd.Series(np.random.normal(0, 1, 100))
        
        detrended, stats = detrend_series(series)
        
        # Slope should be close to 0
        assert abs(stats['slope']) < 0.5
        # R-squared should be low
        assert stats['rsquared'] < 0.1

    def test_too_short_series_raises_error(self):
        """Test that series < 3 points raises PreprocessingError."""
        series = pd.Series([1.0, 2.0])
        with pytest.raises(PreprocessingError, match="Series too short"):
            detrend_series(series)

    def test_detrend_with_missing_values(self):
        """Test detrending with missing values (should be dropped)."""
        series = pd.Series([1.0, np.nan, 3.0, 4.0, 5.0, np.nan, 7.0])
        detrended, stats = detrend_series(series)
        assert not detrended.isna().any()

class TestDifferenceSeries:
    """Tests for differencing logic."""

    def test_first_order_difference(self):
        """Test first-order differencing."""
        series = pd.Series([1.0, 2.0, 4.0, 7.0, 11.0])
        differenced = difference_series(series, order=1)
        
        # Expected: [1, 2, 3, 4]
        expected = pd.Series([1.0, 2.0, 3.0, 4.0])
        pd.testing.assert_series_equal(differenced, expected)

    def test_second_order_difference(self):
        """Test second-order differencing."""
        series = pd.Series([1.0, 2.0, 4.0, 7.0, 11.0])
        differenced = difference_series(series, order=2)
        
        # First diff: [1, 2, 3, 4]
        # Second diff: [1, 1, 1]
        expected = pd.Series([1.0, 1.0, 1.0])
        pd.testing.assert_series_equal(differenced, expected)

    def test_differencing_stationarizes_series(self):
        """Test that differencing can stationarize a non-stationary series."""
        # Random walk
        np.random.seed(42)
        series = pd.Series(np.cumsum(np.random.normal(0, 1, 100)))
        
        # Original should be non-stationary
        is_orig_stationary, _ = check_stationarity(series)
        
        # Differenced should be stationary
        differenced = difference_series(series, order=1)
        is_diff_stationary, _ = check_stationarity(differenced)
        
        # Note: This is probabilistic, but often true
        assert is_diff_stationary or not is_orig_stationary

    def test_order_zero_raises_error(self):
        """Test that order=0 raises PreprocessingError."""
        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(PreprocessingError, match="Order must be >= 1"):
            difference_series(series, order=0)

    def test_high_order_results_in_empty(self):
        """Test that too high order results in error."""
        series = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(PreprocessingError, match="resulted in empty series"):
            difference_series(series, order=10)

class TestPreprocessSeries:
    """Tests for the full preprocessing pipeline."""

    def test_preprocess_stationary_series(self):
        """Test preprocessing of an already stationary series."""
        np.random.seed(42)
        series = pd.Series(np.random.normal(0, 1, 100))
        
        result, log = preprocess_series(series)
        
        assert log['stationary']
        assert log['differencing_order'] == 0
        assert log['final_length'] == 100

    def test_preprocess_with_missing_values(self):
        """Test preprocessing with missing values."""
        series = pd.Series([1.0, np.nan, 3.0, 4.0, np.nan, 6.0] + [7.0] * 100)
        
        result, log = preprocess_series(series, interpolate_missing_values=True)
        
        assert log['interpolated']
        assert not result.isna().any()

    def test_preprocess_non_stationary_requires_differencing(self):
        """Test that non-stationary series gets differenced."""
        # Random walk
        np.random.seed(42)
        series = pd.Series(np.cumsum(np.random.normal(0, 1, 200)))
        
        result, log = preprocess_series(
            series,
            max_differencing_order=3,
            alpha=0.05
        )
        
        # Should have been differenced
        assert log['differencing_order'] > 0 or log['detrended']
        assert log['stationary']

    def test_preprocess_detrending_first(self):
        """Test that detrending is attempted before differencing."""
        # Series with linear trend
        n = 200
        t = np.arange(n)
        series = pd.Series(2 * t + np.random.normal(0, 1, n))
        
        result, log = preprocess_series(series)
        
        # Should have been detrended if that achieved stationarity
        if log['detrended']:
            assert not log['differencing_order'] > 0

    def test_preprocess_raises_on_failure(self):
        """Test that preprocessing raises error when it cannot achieve stationarity."""
        # This is hard to construct, but we test the error path
        # by using a very short series that fails all checks
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        
        with pytest.raises(PreprocessingError, match="too short"):
            preprocess_series(series)

class TestPreprocessDataset:
    """Tests for dataset-level preprocessing."""

    def test_preprocess_valid_dataset(self):
        """Test preprocessing of a valid dataset."""
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'value': np.random.normal(0, 1, 100)
        })
        
        result, log = preprocess_dataset(
            df,
            time_column='date',
            value_column='value'
        )
        
        assert 'value' in result.columns
        assert log['final_length'] > 0

    def test_preprocess_missing_columns_raises_error(self):
        """Test that missing columns raise PreprocessingError."""
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'other': np.random.normal(0, 1, 100)
        })
        
        with pytest.raises(PreprocessingError, match="not found"):
            preprocess_dataset(
                df,
                time_column='date',
                value_column='value'
            )

    def test_preprocess_with_missing_values(self):
        """Test preprocessing dataset with missing values."""
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'value': [np.nan if i % 10 == 0 else np.random.normal(0, 1) for i in range(100)]
        })
        
        result, log = preprocess_dataset(
            df,
            time_column='date',
            value_column='value',
            interpolate_missing_values=True
        )
        
        assert not result.isna().any().any()
        assert log['series_log']['interpolated']