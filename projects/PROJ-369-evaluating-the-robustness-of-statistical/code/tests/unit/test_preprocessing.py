import pytest
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
import sys
from src.data.preprocessing import (
    interpolate_missing, 
    check_stationarity_adf, 
    detrend_linear, 
    difference_series, 
    preprocess_series, 
    preprocess_dataset,
    PreprocessingError
)

class TestInterpolateMissing:
    def test_linear_interpolation(self):
        series = pd.Series([1, 2, np.nan, 4, 5])
        result = interpolate_missing(series)
        assert result[2] == 3.0

    def test_no_missing_values(self):
        series = pd.Series([1, 2, 3, 4, 5])
        result = interpolate_missing(series)
        assert np.allclose(result, series)

class TestCheckStationarity:
    def test_stationary_series(self):
        np.random.seed(42)
        series = pd.Series(np.random.randn(100))
        is_stationary, p_value = check_stationarity_adf(series)
        assert is_stationary is True or p_value < 0.05  # May vary by seed

    def test_non_stationary_series(self):
        # Create a random walk
        np.random.seed(123)
        series = pd.Series(np.cumsum(np.random.randn(100)))
        is_stationary, p_value = check_stationarity_adf(series)
        assert is_stationary is False or p_value >= 0.05

class TestDetrendSeries:
    def test_linear_detrending(self):
        n = 100
        x = np.arange(n)
        y = 2 * x + 5 + np.random.randn(n) * 0.5
        series = pd.Series(y)
        
        detrended = detrend_linear(series)
        
        # Check that detrended series has no trend
        slope, _, _, _, _ = stats.linregress(range(n), detrended.values)
        assert abs(slope) < 0.1  # Slope should be close to zero

class TestDifferenceSeries:
    def test_first_difference(self):
        series = pd.Series([1, 2, 4, 7, 11])
        result = difference_series(series)
        expected = pd.Series([1.0, 2.0, 3.0, 4.0], index=[1, 2, 3, 4])
        assert np.allclose(result.values, expected.values)

    def test_second_difference(self):
        series = pd.Series([1, 2, 4, 7, 11])
        result = difference_series(series, order=2)
        # First diff: [1, 2, 3, 4]
        # Second diff: [1, 1, 1]
        assert len(result) == 3

class TestPreprocessSeries:
    def test_preprocess_stationary(self):
        np.random.seed(42)
        series = pd.Series(np.random.randn(100), index=pd.date_range('2020-01-01', periods=100))
        result = preprocess_series(series)
        
        assert 'processed_series' in result
        assert 'is_stationary' in result
        assert 'differencing_count' in result

    def test_preprocess_non_stationary(self):
        np.random.seed(123)
        series = pd.Series(np.cumsum(np.random.randn(100)), index=pd.date_range('2020-01-01', periods=100))
        result = preprocess_series(series)
        
        assert result['differencing_count'] >= 0

    def test_short_series_skipped(self):
        series = pd.Series(np.random.randn(20), index=pd.date_range('2020-01-01', periods=20))
        result = preprocess_series(series)
        
        assert result['skipped'] is True

class TestPreprocessDataset:
    def test_single_series(self):
        n = 100
        dates = pd.date_range('2020-01-01', periods=n, freq='D')
        df = pd.DataFrame({
            'datetime': dates,
            'value': np.random.randn(n)
        })
        
        result = preprocess_dataset(df)
        assert result is not None
        assert len(result) <= n

    def test_multiple_series(self):
        n = 50
        dates = pd.date_range('2020-01-01', periods=n, freq='D')
        df = pd.DataFrame({
            'datetime': dates.tolist() * 2,
            'value': np.random.randn(n * 2),
            'series_id': ['A'] * n + ['B'] * n
        })
        
        result = preprocess_dataset(df)
        assert result is not None
        assert 'series_id' in result.columns