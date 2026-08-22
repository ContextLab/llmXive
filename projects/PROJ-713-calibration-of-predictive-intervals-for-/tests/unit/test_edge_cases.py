"""
Unit tests for edge cases in the predictive interval calibration pipeline.

Tests cover:
1. Constant variance handling in models (ARIMA, LSTM, Prophet)
2. NaN/Inf handling in metrics and data loading
3. Empty or single-point series handling
4. Extreme value handling (very large/small numbers)
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.arima_model import ARIMAModel
from models.lstm_model import LSTMModel
from models.prophet_model import ProphetModel
from metrics.coverage import compute_coverage, compute_coverage_deviation
from metrics.pit import calculate_pit, ljung_box_test
from metrics.crps import compute_crps
from utils.exceptions import CalibrationError, DataValidationError
from data_loader import split_series, standardize


class TestConstantVariance:
    """Test handling of constant variance series."""

    def test_arima_constant_series(self):
        """ARIMA should handle constant series without crashing."""
        # Create constant series
        constant_data = np.ones(100)
        dates = pd.date_range(start="2020-01-01", periods=100, freq="H")
        series = pd.Series(constant_data, index=dates)
        
        model = ARIMAModel(order=(1, 0, 0))
        
        # Should not raise an exception, but may return warnings
        try:
            model.fit(series)
            forecasts, intervals = model.forecast(steps=10)
            
            # Check that forecasts are reasonable (close to constant)
            assert np.allclose(forecasts, constant_data[0], atol=1e-6)
            
            # Intervals should be valid (no NaN/Inf)
            assert not np.any(np.isnan(intervals))
            assert not np.any(np.isinf(intervals))
        except Exception as e:
            # Some ARIMA implementations may fail on constant series
            # This is acceptable if the error is logged/handled appropriately
            assert isinstance(e, (ValueError, CalibrationError))

    def test_lstm_constant_series(self):
        """LSTM should handle constant series without NaN/Inf outputs."""
        constant_data = np.ones(100)
        dates = pd.date_range(start="2020-01-01", periods=100, freq="H")
        series = pd.Series(constant_data, index=dates)
        
        model = LSTMModel(hidden_size=32, max_epochs=10)
        
        try:
            model.fit(series)
            forecasts, intervals = model.forecast(steps=10)
            
            # Forecasts should be close to constant
            assert np.allclose(forecasts, constant_data[0], atol=1e-3)
            
            # Intervals should be valid
            assert not np.any(np.isnan(intervals))
            assert not np.any(np.isinf(intervals))
        except Exception as e:
            # LSTM may fail on constant series due to lack of variance
            # This is acceptable if properly handled
            assert isinstance(e, (ValueError, CalibrationError))

    def test_prophet_constant_series(self):
        """Prophet should handle constant series."""
        constant_data = np.ones(100)
        dates = pd.date_range(start="2020-01-01", periods=100, freq="H")
        df = pd.DataFrame({"ds": dates, "y": constant_data})
        
        model = ProphetModel()
        
        try:
            model.fit(df)
            future = model.make_future_dataframe(periods=10)
            forecast = model.predict(future)
            
            # Check forecasts are reasonable
            assert np.allclose(forecast["yhat"].tail(10), constant_data[0], atol=1e-3)
            
            # Check intervals are valid
            assert not np.any(np.isnan(forecast["yhat_lower"].tail(10)))
            assert not np.any(np.isnan(forecast["yhat_upper"].tail(10)))
        except Exception as e:
            # Prophet may issue warnings or fail on constant series
            assert isinstance(e, (ValueError, CalibrationError))

class TestNaNHandling:
    """Test handling of NaN and Inf values."""

    def test_coverage_with_nan_forecasts(self):
        """Coverage calculation should handle NaN forecasts gracefully."""
        true_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        forecasts = np.array([1.1, np.nan, 3.1, 4.1, 5.1])
        lower = np.array([0.5, 1.0, 2.0, 3.0, 4.0])
        upper = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
        
        # Should handle NaN without crashing
        coverage = compute_coverage(true_values, forecasts, lower, upper, nominal_level=0.8)
        
        # Coverage should be calculated on non-NaN points
        assert 0.0 <= coverage <= 1.0

    def test_coverage_with_inf_intervals(self):
        """Coverage calculation should handle infinite intervals."""
        true_values = np.array([1.0, 2.0, 3.0])
        forecasts = np.array([1.1, 2.1, 3.1])
        lower = np.array([-np.inf, 1.0, 2.0])
        upper = np.array([np.inf, 3.0, 4.0])
        
        coverage = compute_coverage(true_values, forecasts, lower, upper, nominal_level=0.8)
        
        # Should handle infinite bounds
        assert 0.0 <= coverage <= 1.0

    def test_pit_with_nan(self):
        """PIT calculation should handle NaN values."""
        true_values = np.array([1.0, 2.0, np.nan, 4.0])
        forecasts = np.array([1.1, 2.1, 3.1, 4.1])
        residuals = np.array([0.1, 0.1, 0.1, 0.1])
        
        # Should handle NaN without crashing
        pit_values = calculate_pit(true_values, forecasts, residuals)
        
        # PIT should be valid for non-NaN points
        assert len(pit_values) == len(true_values)
        assert not np.any(np.isnan(pit_values[:2]))

    def test_crps_with_nan(self):
        """CRPS calculation should handle NaN values."""
        true_values = np.array([1.0, 2.0, np.nan, 4.0])
        forecasts = np.array([[1.0, 1.1, 1.2], [2.0, 2.1, 2.2], [3.0, 3.1, 3.2], [4.0, 4.1, 4.2]])
        
        # Should handle NaN without crashing
        crps_values = compute_crps(true_values, forecasts)
        
        # CRPS should be valid for non-NaN points
        assert len(crps_values) == len(true_values)

class TestEmptyAndSinglePointSeries:
    """Test handling of empty or single-point series."""

    def test_arima_empty_series(self):
        """ARIMA should handle empty series gracefully."""
        empty_series = pd.Series([], dtype=float)
        
        model = ARIMAModel(order=(1, 0, 0))
        
        with pytest.raises((ValueError, CalibrationError, DataValidationError)):
            model.fit(empty_series)

    def test_arima_single_point(self):
        """ARIMA should handle single-point series gracefully."""
        single_point = pd.Series([1.0])
        
        model = ARIMAModel(order=(1, 0, 0))
        
        with pytest.raises((ValueError, CalibrationError, DataValidationError)):
            model.fit(single_point)

    def test_lstm_empty_series(self):
        """LSTM should handle empty series gracefully."""
        empty_series = pd.Series([], dtype=float)
        
        model = LSTMModel(hidden_size=32, max_epochs=10)
        
        with pytest.raises((ValueError, CalibrationError, DataValidationError)):
            model.fit(empty_series)

    def test_prophet_empty_df(self):
        """Prophet should handle empty DataFrame gracefully."""
        empty_df = pd.DataFrame({"ds": [], "y": []})
        
        model = ProphetModel()
        
        with pytest.raises((ValueError, CalibrationError, DataValidationError)):
            model.fit(empty_df)

class TestExtremeValues:
    """Test handling of extreme values."""

    def test_very_large_values(self):
        """Models should handle very large values without overflow."""
        large_data = np.array([1e10, 1e10 + 1, 1e10 + 2, 1e10 + 3, 1e10 + 4])
        dates = pd.date_range(start="2020-01-01", periods=5, freq="H")
        series = pd.Series(large_data, index=dates)
        
        model = ARIMAModel(order=(1, 0, 0))
        
        try:
            model.fit(series)
            forecasts, intervals = model.forecast(steps=2)
            
            # Check that forecasts are reasonable
            assert not np.any(np.isnan(forecasts))
            assert not np.any(np.isinf(forecasts))
        except Exception as e:
            # Some models may struggle with extreme values
            assert isinstance(e, (ValueError, CalibrationError))

    def test_very_small_values(self):
        """Models should handle very small values without underflow."""
        small_data = np.array([1e-10, 1e-10 + 1e-12, 1e-10 + 2e-12, 1e-10 + 3e-12])
        dates = pd.date_range(start="2020-01-01", periods=4, freq="H")
        series = pd.Series(small_data, index=dates)
        
        model = ARIMAModel(order=(1, 0, 0))
        
        try:
            model.fit(series)
            forecasts, intervals = model.forecast(steps=2)
            
            # Check that forecasts are reasonable
            assert not np.any(np.isnan(forecasts))
            assert not np.any(np.isinf(forecasts))
        except Exception as e:
            # Some models may struggle with extreme values
            assert isinstance(e, (ValueError, CalibrationError))

    def test_mixed_extreme_values(self):
        """Models should handle series with mixed extreme values."""
        mixed_data = np.array([1e10, 1e-10, 1e10, 1e-10, 1e10])
        dates = pd.date_range(start="2020-01-01", periods=5, freq="H")
        series = pd.Series(mixed_data, index=dates)
        
        model = ARIMAModel(order=(1, 0, 0))
        
        try:
            model.fit(series)
            forecasts, intervals = model.forecast(steps=2)
            
            # Check that forecasts are reasonable
            assert not np.any(np.isnan(forecasts))
            assert not np.any(np.isinf(forecasts))
        except Exception as e:
            # Some models may struggle with mixed extreme values
            assert isinstance(e, (ValueError, CalibrationError))

class TestDataLoaderEdgeCases:
    """Test edge cases in data loading and preprocessing."""

    def test_split_series_empty(self):
        """split_series should handle empty series."""
        empty_series = pd.Series([], dtype=float)
        
        with pytest.raises((ValueError, DataValidationError)):
            split_series(empty_series, train_ratio=0.8)

    def test_split_series_single_point(self):
        """split_series should handle single-point series."""
        single_point = pd.Series([1.0])
        
        with pytest.raises((ValueError, DataValidationError)):
            split_series(single_point, train_ratio=0.8)

    def test_standardize_constant_series(self):
        """standardize should handle constant series."""
        constant_data = np.ones(100)
        
        standardized = standardize(constant_data)
        
        # For constant series, standard deviation is 0
        # Standardization should handle this gracefully
        assert len(standardized) == len(constant_data)

    def test_standardize_with_nan(self):
        """standardize should handle series with NaN values."""
        data_with_nan = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        
        standardized = standardize(data_with_nan)
        
        # Should handle NaN without crashing
        assert len(standardized) == len(data_with_nan)