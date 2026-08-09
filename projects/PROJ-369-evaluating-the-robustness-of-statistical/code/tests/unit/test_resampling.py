"""
Unit tests for resampling logic in src.data.resampling.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import timedelta

from src.data.resampling import (
    detect_native_frequency,
    determine_target_frequency,
    resample_series,
    resample_dataset,
    PreprocessingError
)


@pytest.fixture
def sub_hourly_data():
    """Create a DataFrame with 15-minute intervals."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='15T')
    values = np.random.randn(100)
    return pd.DataFrame({'datetime': dates, 'value': values})


@pytest.fixture
def hourly_data():
    """Create a DataFrame with hourly intervals."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
    values = np.random.randn(100)
    return pd.DataFrame({'datetime': dates, 'value': values})


@pytest.fixture
def daily_data():
    """Create a DataFrame with daily intervals."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    values = np.random.randn(100)
    return pd.DataFrame({'datetime': dates, 'value': values})


class TestDetectNativeFrequency:
    def test_detect_sub_hourly_frequency(self, sub_hourly_data):
        freq = detect_native_frequency(sub_hourly_data, 'datetime')
        assert freq == '15T'
    
    def test_detect_hourly_frequency(self, hourly_data):
        freq = detect_native_frequency(hourly_data, 'datetime')
        assert freq == 'H'
    
    def test_detect_daily_frequency(self, daily_data):
        freq = detect_native_frequency(daily_data, 'datetime')
        assert freq == 'D'
    
    def test_insufficient_data(self):
        dates = pd.date_range(start='2023-01-01', periods=2, freq='H')
        df = pd.DataFrame({'datetime': dates, 'value': [1, 2]})
        with pytest.raises(PreprocessingError, match="Insufficient data points"):
            detect_native_frequency(df, 'datetime')


class TestDetermineTargetFrequency:
    def test_sub_hourly_to_hourly(self):
        assert determine_target_frequency('15T') == 'H'
        assert determine_target_frequency('30T') == 'H'
        assert determine_target_frequency('T') == 'H'
    
    def test_hourly_to_daily(self):
        assert determine_target_frequency('H') == 'D'
        assert determine_target_frequency('4H') == 'D'
        assert determine_target_frequency('12H') == 'D'
    
    def test_daily_to_daily(self):
        assert determine_target_frequency('D') == 'D'
    
    def test_coarser_frequency(self):
        # Should return native frequency and log warning (we can't easily test log in unit test without mocking)
        assert determine_target_frequency('W') == 'W'
        assert determine_target_frequency('M') == 'M'


class TestResampleSeries:
    def test_resample_sub_hourly_to_hourly(self, sub_hourly_data):
        df_resampled = resample_series(
            sub_hourly_data, 'H', 'value', 'datetime', 'mean'
        )
        # 100 points at 15min -> 25 hours (approx)
        assert len(df_resampled) == 25
        assert df_resampled.index.freq == pd.Timedelta(hours=1)
    
    def test_resample_hourly_to_daily(self, hourly_data):
        df_resampled = resample_series(
            hourly_data, 'D', 'value', 'datetime', 'mean'
        )
        # 100 hours -> 4 days + 4 hours -> 4 or 5 days depending on alignment
        # With 'H' starting at 00:00, 100 hours is 4 days and 4 hours.
        # Resampling to 'D' will give 5 days (00:00 to 04:00 on day 5 is in day 5 bucket? No, 04:00 is in day 5 if freq is D)
        # Actually, 100 hours from 2023-01-01 00:00 is 2023-01-05 04:00.
        # Resampling to D:
        # 2023-01-01, 2023-01-02, 2023-01-03, 2023-01-04, 2023-01-05 (partial)
        # So 5 days.
        assert len(df_resampled) == 5
        assert df_resampled.index.freq == pd.Timedelta(days=1)
    
    def test_missing_value_column(self, hourly_data):
        with pytest.raises(PreprocessingError, match="Value column 'invalid' not found"):
            resample_series(hourly_data, 'D', 'invalid', 'datetime')
    
    def test_invalid_datetime_index(self):
        df = pd.DataFrame({'value': [1, 2, 3]})
        with pytest.raises(PreprocessingError, match="DataFrame must have a DatetimeIndex"):
            resample_series(df, 'D', 'value')


class TestResampleDataset:
    def test_full_resample_pipeline(self, sub_hourly_data):
        resampled_df, native, target = resample_dataset(
            sub_hourly_data, 'value', 'datetime'
        )
        assert native == '15T'
        assert target == 'H'
        assert len(resampled_df) == 25
        assert 'value' in resampled_df.columns
    
    def test_no_resample_needed(self, daily_data):
        resampled_df, native, target = resample_dataset(
            daily_data, 'value', 'datetime'
        )
        assert native == 'D'
        assert target == 'D'
        # Should be same length if no resampling happened
        assert len(resampled_df) == 100
    
    def test_coarser_frequency_handling(self):
        dates = pd.date_range(start='2023-01-01', periods=100, freq='W')
        df = pd.DataFrame({'datetime': dates, 'value': np.random.randn(100)})
        resampled_df, native, target = resample_dataset(df, 'value', 'datetime')
        assert native == 'W'
        assert target == 'W' # Should keep native
        assert len(resampled_df) == 100