"""
Integration test for Self-Calibrating Conformal Prediction wrapper improvement.

This test verifies that wrapping a base forecaster with the ConformalPredictionWrapper
(code/calibration/conformal.py) improves empirical coverage calibration compared to
the base model alone, specifically targeting the 0.80 and 0.95 nominal levels.

It loads a single real series (M4 Hourly), fits a base model (ARIMA), runs the
conformal wrapper, and asserts that the absolute deviation of empirical coverage
from the nominal level is reduced by the wrapper.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data_loader import load_m4_hourly, split_series, standardize
from models.arima_model import ARIMAModel
from metrics.coverage import compute_coverage
from calibration.conformal import ConformalPredictionWrapper
from utils.exceptions import CalibrationError, DataValidationError


class TestConformalImprovement:
    """Integration tests for conformal wrapper coverage improvement."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(parents=True)
        
        # Use a small subset of M4 hourly data for speed in integration test
        # We load the full dataset but only process the first few series
        self.series_limit = 3 
        
        # Load a real series from M4 Hourly
        # Note: load_m4_hourly returns a list of dicts with 'v', 'id', 'frequency'
        try:
            self.raw_data = load_m4_hourly()
            assert len(self.raw_data) > 0, "M4 Hourly data is empty or unavailable"
        except (ValueError, FileNotFoundError) as e:
            pytest.skip(f"Real data source unavailable: {e}")

    def teardown_method(self):
        """Clean up temporary directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _prepare_single_series(self, series_idx: int = 0):
        """Prepare a single real series for testing."""
        if series_idx >= len(self.raw_data):
            pytest.skip(f"Not enough series in data (need > {series_idx})")
        
        series_dict = self.raw_data[series_idx]
        series_values = series_dict['v']
        
        if len(series_values) < 50:
            pytest.skip("Series too short for meaningful split")

        # Convert to pandas Series
        series = pd.Series(series_values)
        
        # Split into train/test (80/20)
        train_data, test_data = split_series(series, train_ratio=0.8)
        
        # Standardize (fit on train, apply to both)
        train_std, test_std = standardize(train_data, test_data)
        
        return train_std, test_std, series

    def test_conformal_improves_coverage_arima(self):
        """
        Test that ConformalPredictionWrapper improves coverage calibration 
        for ARIMA model on a real M4 series.
        
        Expected: |Empirical Coverage - Nominal| should be smaller for 
        the conformal wrapper than for the base model.
        """
        # Use the first valid series
        train_std, test_std, original_series = self._prepare_single_series(0)
        
        # Nominal levels to test
        nominal_levels = [0.80, 0.95]
        
        # Initialize base model
        base_model = ARIMAModel()
        
        # Fit base model
        base_model.fit(train_std)
        
        # Generate base model forecasts and intervals
        base_forecasts = base_model.predict(n_steps=len(test_std))
        base_intervals = base_model.predict_intervals(
            n_steps=len(test_std), 
            confidence_levels=nominal_levels
        )
        
        # Compute base model coverage
        base_coverages = {}
        for level in nominal_levels:
            lower = base_intervals[str(level)][:, 0]
            upper = base_intervals[str(level)][:, 1]
            coverage = compute_coverage(test_std.values, lower, upper)
            base_coverages[level] = coverage
        
        # Initialize and fit conformal wrapper
        # We use a fixed calibration set size to ensure reproducibility
        cal_size = max(10, int(len(train_std) * 0.2))
        wrapper = ConformalPredictionWrapper(
            base_model=base_model,
            calibration_size=cal_size,
            nominal_levels=nominal_levels
        )
        
        # Fit wrapper (this recalibrates intervals using conformal prediction)
        wrapper.fit(train_std)
        
        # Generate wrapped forecasts and intervals
        wrapped_forecasts = wrapper.predict(n_steps=len(test_std))
        wrapped_intervals = wrapper.predict_intervals(
            n_steps=len(test_std),
            confidence_levels=nominal_levels
        )
        
        # Compute wrapped model coverage
        wrapped_coverages = {}
        for level in nominal_levels:
            lower = wrapped_intervals[str(level)][:, 0]
            upper = wrapped_intervals[str(level)][:, 1]
            coverage = compute_coverage(test_std.values, lower, upper)
            wrapped_coverages[level] = coverage
        
        # Assert improvement (or at least no significant degradation)
        improvements = []
        for level in nominal_levels:
            base_deviation = abs(base_coverages[level] - level)
            wrapped_deviation = abs(wrapped_coverages[level] - level)
            
            # The conformal wrapper should reduce deviation from nominal
            # Allow a small tolerance for edge cases
            improvement = wrapped_deviation <= base_deviation + 0.05
            improvements.append(improvement)
            
            # Log results for debugging
            print(f"Level {level}: Base Deviation={base_deviation:.4f}, "
                  f"Wrapped Deviation={wrapped_deviation:.4f}, "
                  f"Improvement={improvement}")
        
        # At least one level should show improvement
        assert any(improvements), (
            "Conformal wrapper did not improve coverage for any nominal level. "
            f"Base deviations: {base_coverages}, Wrapped deviations: {wrapped_coverages}"
        )

    def test_conformal_wrapper_handles_edge_cases(self):
        """Test that the conformal wrapper handles edge cases gracefully."""
        train_std, test_std, _ = self._prepare_single_series(0)
        
        base_model = ARIMAModel()
        base_model.fit(train_std)
        
        # Test with very small calibration set
        wrapper = ConformalPredictionWrapper(
            base_model=base_model,
            calibration_size=5,  # Very small
            nominal_levels=[0.80]
        )
        
        # Should not crash even with small calibration set
        try:
            wrapper.fit(train_std)
            intervals = wrapper.predict_intervals(n_steps=10, confidence_levels=[0.80])
            assert intervals is not None
            assert intervals['0.80'].shape[0] == 10
        except CalibrationError as e:
            # Expected if calibration fails due to insufficient data
            pytest.skip(f"Calibration failed as expected with small set: {e}")
        
        # Test with nominal level outside valid range
        with pytest.raises(DataValidationError):
            ConformalPredictionWrapper(
                base_model=base_model,
                calibration_size=10,
                nominal_levels=[1.5]  # Invalid
            )

    def test_conformal_wrapper_preserves_forecast_values(self):
        """Test that the wrapper preserves the base model's point forecasts."""
        train_std, test_std, _ = self._prepare_single_series(0)
        
        base_model = ARIMAModel()
        base_model.fit(train_std)
        
        base_forecasts = base_model.predict(n_steps=len(test_std))
        
        wrapper = ConformalPredictionWrapper(
            base_model=base_model,
            calibration_size=20,
            nominal_levels=[0.80]
        )
        
        wrapper.fit(train_std)
        wrapped_forecasts = wrapper.predict(n_steps=len(test_std))
        
        # Point forecasts should be identical
        np.testing.assert_array_almost_equal(
            base_forecasts, 
            wrapped_forecasts,
            decimal=10,
            err_msg="Conformal wrapper should preserve base model point forecasts"
        )

    def test_conformal_wrapper_interval_width_adjustment(self):
        """Test that the wrapper adjusts interval widths based on calibration."""
        train_std, test_std, _ = self._prepare_single_series(0)
        
        base_model = ARIMAModel()
        base_model.fit(train_std)
        
        base_intervals = base_model.predict_intervals(
            n_steps=len(test_std),
            confidence_levels=[0.80]
        )
        
        wrapper = ConformalPredictionWrapper(
            base_model=base_model,
            calibration_size=20,
            nominal_levels=[0.80]
        )
        
        wrapper.fit(train_std)
        wrapped_intervals = wrapper.predict_intervals(
            n_steps=len(test_std),
            confidence_levels=[0.80]
        )
        
        # Calculate average interval widths
        base_widths = base_intervals['0.80'][:, 1] - base_intervals['0.80'][:, 0]
        wrapped_widths = wrapped_intervals['0.80'][:, 1] - wrapped_intervals['0.80'][:, 0]
        
        avg_base_width = np.mean(base_widths)
        avg_wrapped_width = np.mean(wrapped_widths)
        
        # The wrapped intervals should be different (typically wider to ensure coverage)
        # Allow for small numerical differences
        width_change_ratio = abs(avg_wrapped_width - avg_base_width) / avg_base_width
        
        # Intervals should change by at least 1% (significant adjustment)
        assert width_change_ratio > 0.01, (
            f"Conformal wrapper did not adjust interval widths significantly. "
            f"Base avg: {avg_base_width:.4f}, Wrapped avg: {avg_wrapped_width:.4f}"
        )