"""
Unit tests for src/data/preprocessing.py.
Verifies ADF logic, differencing loops, detrending, and missing value interpolation.
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
import sys
import os

# Ensure src is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.preprocessing import (
    PreprocessingError,
    interpolate_missing,
    check_stationarity,
    detrend_series,
    difference_series,
    preprocess_series,
    preprocess_dataset,
    check_stationarity_adf,
    detrend_linear,
    difference,
    preprocess
)


class TestInterpolateMissing:
    def test_interpolate_linear(self):
        """Test linear interpolation for missing values."""
        series = pd.Series([1.0, np.nan, np.nan, 4.0, 5.0])
        result = interpolate_missing(series)
        assert not result.isna().any(), "All NaNs should be interpolated"
        assert result.iloc[1] == 2.0, "First interpolated value should be 2.0"
        assert result.iloc[2] == 3.0, "Second interpolated value should be 3.0"

    def test_interpolate_edges_unchanged(self):
        """Test that NaNs at edges are not interpolated (remain NaN)."""
        series = pd.Series([np.nan, 2.0, 3.0, np.nan])
        result = interpolate_missing(series)
        assert pd.isna(result.iloc[0]), "Leading NaN should remain"
        assert pd.isna(result.iloc[3]), "Trailing NaN should remain"
        assert result.iloc[1] == 2.0
        assert result.iloc[2] == 3.0

    def test_no_missing_values(self):
        """Test that a series without missing values is returned unchanged."""
        series = pd.Series([1.0, 2.0, 3.0])
        result = interpolate_missing(series)
        pd.testing.assert_series_equal(result, series)


class TestCheckStationarity:
    def test_stationary_series(self):
        """Test ADF on a known stationary series (white noise)."""
        np.random.seed(42)
        stationary = pd.Series(np.random.normal(0, 1, 200))
        is_stationary, p_value = check_stationarity_adf(stationary, alpha=0.05)
        assert is_stationary, "White noise should be stationary (p < 0.05)"
        assert p_value < 0.05

    def test_non_stationary_series(self):
        """Test ADF on a random walk (non-stationary)."""
        np.random.seed(42)
        walk = pd.Series(np.random.normal(0, 1, 200)).cumsum()
        is_stationary, p_value = check_stationarity_adf(walk, alpha=0.05)
        assert not is_stationary, "Random walk should be non-stationary (p >= 0.05)"
        assert p_value >= 0.05

    def test_trend_series(self):
        """Test ADF on a linear trend (non-stationary)."""
        trend = pd.Series(np.linspace(0, 100, 200))
        is_stationary, p_value = check_stationarity_adf(trend, alpha=0.05)
        assert not is_stationary, "Linear trend should be non-stationary"


class TestDetrendSeries:
    def test_detrend_linear(self):
        """Test detrending a linear series leaves residuals near zero."""
        x = np.arange(100)
        y = 2 * x + 5 + np.random.normal(0, 0.1, 100)
        residuals = detrend_linear(y)
        assert np.abs(residuals.mean()) < 0.1, "Residual mean should be near zero"
        assert residuals.std() < 1.0, "Residual std should be small"

    def test_detrend_constant(self):
        """Test detrending a constant series."""
        const = pd.Series([5.0] * 100)
        residuals = detrend_linear(const)
        assert np.allclose(residuals, 0.0), "Residuals of constant should be zero"


class TestDifferenceSeries:
    def test_difference_once(self):
        """Test first-order differencing."""
        series = pd.Series([1, 2, 4, 7, 11])
        diff = difference_series(series, order=1)
        expected = pd.Series([1, 2, 3, 4], index=range(1, 5))
        pd.testing.assert_series_equal(diff, expected)

    def test_difference_twice(self):
        """Test second-order differencing."""
        series = pd.Series([1, 2, 4, 7, 11])
        diff = difference_series(series, order=2)
        # First diff: [1, 2, 3, 4]
        # Second diff: [1, 1, 1]
        expected = pd.Series([1, 1, 1], index=range(2, 5))
        pd.testing.assert_series_equal(diff, expected)

    def test_difference_order_exceeds_length(self):
        """Test that differencing beyond length raises PreprocessingError."""
        series = pd.Series([1, 2, 3])
        with pytest.raises(PreprocessingError):
            difference_series(series, order=5)


class TestPreprocessSeries:
    def test_preprocess_stationary_no_op(self):
        """Test preprocessing a stationary series (no differencing/detrending)."""
        np.random.seed(42)
        stationary = pd.Series(np.random.normal(0, 1, 200))
        result, path = preprocess_series(stationary)
        assert path == "none", "Stationary series should require no transformation"
        np.testing.assert_array_almost_equal(result.values, stationary.values)

    def test_preprocess_trend_detrend(self):
        """Test preprocessing a linear trend (should detrend)."""
        x = np.arange(100)
        y = 2 * x + 5 + np.random.normal(0, 0.1, 100)
        series = pd.Series(y)
        result, path = preprocess_series(series)
        assert path == "detrend", "Trend series should be detrended"
        # Check that result is stationary
        is_stat, p_val = check_stationarity_adf(result)
        assert is_stat, "Detrended series should be stationary"

    def test_preprocess_random_walk_diff(self):
        """Test preprocessing a random walk (should difference)."""
        np.random.seed(42)
        walk = pd.Series(np.random.normal(0, 1, 200)).cumsum()
        result, path = preprocess_series(walk)
        assert path == "difference", "Random walk should be differenced"
        # Check that result is stationary
        is_stat, p_val = check_stationarity_adf(result)
        assert is_stat, "Differenced random walk should be stationary"

    def test_preprocess_missing_then_diff(self):
        """Test preprocessing with missing values then differencing."""
        np.random.seed(42)
        walk = pd.Series(np.random.normal(0, 1, 200)).cumsum()
        walk.iloc[10] = np.nan
        walk.iloc[50] = np.nan
        result, path = preprocess_series(walk)
        assert "interpolate" in path or path.startswith("difference"), \
            "Should handle missing values"
        assert not result.isna().any(), "Result should have no missing values"
        is_stat, p_val = check_stationarity_adf(result)
        assert is_stat, "Final result should be stationary"

    def test_preprocess_edge_case_short_series(self):
        """Test preprocessing a very short series (< 25 points)."""
        short = pd.Series([1, 2, 3, 4, 5])
        with pytest.raises(PreprocessingError):
            preprocess_series(short)


class TestPreprocessDataset:
    def test_preprocess_dataset_dict(self):
        """Test preprocessing a dictionary of datasets."""
        data = {
            "stationary": pd.Series(np.random.normal(0, 1, 200)),
            "trend": pd.Series(np.arange(200) * 2),
            "walk": pd.Series(np.random.normal(0, 1, 200)).cumsum()
        }
        results = preprocess_dataset(data)
        assert "stationary" in results
        assert "trend" in results
        assert "walk" in results
        assert results["stationary"]["path"] == "none"
        assert results["trend"]["path"] == "detrend"
        assert results["walk"]["path"] == "difference"

    def test_preprocess_dataset_dataframe(self):
        """Test preprocessing a DataFrame with a value column."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2020-01-01", periods=200),
            "value": np.random.normal(0, 1, 200).cumsum()
        })
        result_df, path = preprocess_dataset(df, value_col="value")
        assert "value" in result_df.columns
        assert not result_df["value"].isna().any()
        is_stat, p_val = check_stationarity_adf(result_df["value"])
        assert is_stat, "Preprocessed DataFrame should be stationary"

    def test_preprocess_dataset_invalid_input(self):
        """Test preprocessing invalid input raises error."""
        with pytest.raises(PreprocessingError):
            preprocess_dataset("not a series or dict")

    def test_preprocess_dataset_short_series_skip(self):
        """Test that short series are skipped with a warning."""
        data = {
            "long": pd.Series(np.random.normal(0, 1, 200)),
            "short": pd.Series([1, 2, 3])
        }
        # Should not raise, but skip short
        results = preprocess_dataset(data)
        assert "long" in results
        assert "short" not in results  # Skipped