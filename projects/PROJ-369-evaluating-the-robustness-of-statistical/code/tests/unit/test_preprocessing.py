import pytest
import pandas as pd
import numpy as np
from scipy import stats
from src.data.preprocessing import (
    handle_missing_values, 
    check_stationarity_adf, 
    make_stationary, 
    resample_uk_load_data,
    process_series_for_stationarity
)
from src.utils.config import set_seed

set_seed(42)

class TestPreprocessing:
    
    def test_handle_missing_values_interpolation(self):
        """Test that missing values are linearly interpolated."""
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        data = [1.0, 2.0, np.nan, 4.0, 5.0, np.nan, np.nan, 8.0, 9.0, 10.0]
        df = pd.DataFrame({'value': data}, index=dates)
        
        result = handle_missing_values(df, 'value')
        
        # Check no NaNs remain
        assert result['value'].isna().sum() == 0
        
        # Check interpolation values (approximate)
        # Index 2: between 2 and 4 -> 3.0
        # Index 5, 6: between 5 and 8 -> 6.0, 7.0
        assert result['value'].iloc[2] == 3.0
        assert result['value'].iloc[5] == 6.0
        assert result['value'].iloc[6] == 7.0

    def test_check_stationarity_adf_stationary(self):
        """Test ADF on a stationary series (white noise)."""
        np.random.seed(42)
        stationary_data = pd.Series(np.random.normal(0, 1, 1000))
        
        stat, p_val = check_stationarity_adf(stationary_data)
        
        # White noise should be stationary (p < 0.05)
        assert p_val < 0.05, f"Expected stationary (p < 0.05), got p={p_val}"

    def test_check_stationarity_adf_non_stationary(self):
        """Test ADF on a non-stationary series (random walk)."""
        np.random.seed(42)
        random_walk = pd.Series(np.cumsum(np.random.normal(0, 1, 1000)))
        
        stat, p_val = check_stationarity_adf(random_walk)
        
        # Random walk should be non-stationary (p >= 0.05)
        assert p_val >= 0.05, f"Expected non-stationary (p >= 0.05), got p={p_val}"

    def test_make_stationary_detrend(self):
        """Test detrending when series is already stationary (p < 0.05)."""
        # Create a series with a slight trend but stationary residuals
        # Actually, if it's stationary, we detrend.
        # Let's create a series that is stationary around a trend line
        # A simple linear trend + noise is NOT stationary (mean changes).
        # But ADF might reject the null of unit root if the trend is deterministic.
        # However, the task says: If p < 0.05, detrend.
        # So we need a series where ADF says stationary.
        # White noise is stationary.
        np.random.seed(42)
        data = pd.Series(np.random.normal(0, 1, 1000))
        
        processed, log_info = make_stationary(data, "test_series")
        
        assert log_info["action_taken"] == "detrend"
        assert log_info["detrend_applied"] is True
        # The residuals of a constant mean series should be the series minus a small slope
        assert len(processed) == len(data)

    def test_make_stationary_difference(self):
        """Test differencing when series is non-stationary (p >= 0.05)."""
        # Random walk
        np.random.seed(42)
        random_walk = pd.Series(np.cumsum(np.random.normal(0, 1, 1000)))
        
        processed, log_info = make_stationary(random_walk, "random_walk")
        
        assert log_info["action_taken"] == "difference"
        assert log_info["differences_applied"] >= 1
        # The differenced series should be stationary
        final_stat, final_p = check_stationarity_adf(processed)
        assert final_p < 0.05, "Differenced series should be stationary"

    def test_resample_uk_load_data(self):
        """Test resampling to hourly frequency."""
        # Create irregular datetime index
        dates = pd.DatetimeIndex([
            '2023-01-01 00:00:00',
            '2023-01-01 00:30:00',
            '2023-01-01 01:15:00',
            '2023-01-01 02:00:00',
            '2023-01-01 02:45:00'
        ])
        data = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0], index=dates)
        
        resampled = resample_uk_load_data(data, 'H')
        
        # Check frequency
        assert resampled.index.freq is not None
        assert resampled.index.freqstr == 'H'
        
        # Check length (should be fewer or equal, aggregated)
        assert len(resampled) <= len(data)
        
        # Check no NaNs (if interpolation was applied in resample logic)
        # Our resample_uk_load_data calls interpolate
        assert resampled.isna().sum() == 0

    def test_process_series_for_stationarity_uk_grid(self):
        """End-to-end test for UK National Grid style data processing."""
        # Simulate 30-min data for 2 days
        dates = pd.date_range(start='2023-01-01', periods=96, freq='30T')
        # Create a random walk to ensure non-stationarity
        np.random.seed(42)
        values = np.cumsum(np.random.normal(0, 1, 96))
        series = pd.Series(values, index=dates)
        
        processed, log_info = process_series_for_stationarity(series, "UK_Load_Test")
        
        assert log_info["resampled"] is True
        # Since it was a random walk, it should be differenced
        assert log_info["action_taken"] == "difference"
        assert log_info["differences_applied"] >= 1

    def test_short_series_handling(self):
        """Test that series < 25 points raise an error."""
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        data = pd.Series(np.random.normal(0, 1, 20), index=dates)
        
        with pytest.raises(ValueError, match="too short"):
            check_stationarity_adf(data)

        with pytest.raises(ValueError, match="fewer than 25 points"):
            make_stationary(data, "short_series")