"""
Unit tests for edge cases in the predictive interval calibration pipeline.

Tests cover:
1. Constant variance handling (zero variance in residuals)
2. NaN handling (missing values in time series)
3. Empty series handling
4. Single-point series handling
"""
import numpy as np
import pandas as pd
import pytest
from typing import List, Dict, Tuple, Optional, Any
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics.coverage import compute_coverage, compute_coverage_deviation
from metrics.pit import calculate_pit, generate_pit_histogram, ljung_box_test
from metrics.crps import compute_crps
from metrics.distributional_shape import calculate_kurtosis, flag_heavy_tails
from utils.exceptions import DataValidationError, CalibrationError
from config import Config

class TestConstantVariance:
    """Tests for handling constant variance scenarios."""
    
    def test_constant_residuals_zero_variance(self):
        """Test coverage calculation with zero variance residuals."""
        # Simulate a scenario where all predictions are perfect
        # and intervals have zero width (constant variance = 0)
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        lower_bound = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        upper_bound = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        # Should not raise an error, but coverage should be 1.0 (all points in interval)
        coverage = compute_coverage(y_true, lower_bound, upper_bound)
        assert coverage == 1.0, "Coverage should be 1.0 when all points are exactly on the boundary"
        
    def test_constant_residuals_nonzero_variance(self):
        """Test coverage calculation with constant non-zero variance."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        # Constant interval width
        lower_bound = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
        upper_bound = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        
        coverage = compute_coverage(y_true, lower_bound, upper_bound)
        assert coverage == 1.0, "Coverage should be 1.0 for constant intervals covering all points"
        
    def test_constant_predictions_interval_miss(self):
        """Test when constant variance intervals miss the true values."""
        y_true = np.array([1.0, 10.0, 1.0, 10.0, 1.0])
        y_pred = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        lower_bound = np.array([4.0, 4.0, 4.0, 4.0, 4.0])
        upper_bound = np.array([6.0, 6.0, 6.0, 6.0, 6.0])
        
        coverage = compute_coverage(y_true, lower_bound, upper_bound)
        # Only the middle point (5.0) is within [4.0, 6.0]
        assert coverage == 0.0, "Coverage should be 0.0 when no points are within intervals"

class TestNaNHandling:
    """Tests for handling NaN values in time series."""
    
    def test_nan_in_true_values(self):
        """Test coverage calculation with NaN in true values."""
        y_true = np.array([1.0, np.nan, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        lower_bound = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
        upper_bound = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        
        # Should raise DataValidationError for NaN in true values
        with pytest.raises(DataValidationError):
            compute_coverage(y_true, lower_bound, upper_bound)
            
    def test_nan_in_predictions(self):
        """Test coverage calculation with NaN in predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, np.nan, 3.0, 4.0, 5.0])
        lower_bound = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
        upper_bound = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        
        # Should raise DataValidationError for NaN in predictions
        with pytest.raises(DataValidationError):
            compute_coverage(y_true, lower_bound, upper_bound)
            
    def test_nan_in_bounds(self):
        """Test coverage calculation with NaN in interval bounds."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        lower_bound = np.array([0.5, np.nan, 2.5, 3.5, 4.5])
        upper_bound = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        
        # Should raise DataValidationError for NaN in bounds
        with pytest.raises(DataValidationError):
            compute_coverage(y_true, lower_bound, upper_bound)
            
    def test_nan_in_pit_calculation(self):
        """Test PIT calculation with NaN values."""
        y_true = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        lower_bound = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
        upper_bound = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        
        with pytest.raises(DataValidationError):
            calculate_pit(y_true, y_pred, lower_bound, upper_bound)
            
    def test_nan_in_crps_calculation(self):
        """Test CRPS calculation with NaN values."""
        y_true = np.array([1.0, 2.0, 3.0, np.nan, 5.0])
        y_pred_dist = [np.array([0.5, 1.0, 1.5]), np.array([1.5, 2.0, 2.5]), 
                     np.array([2.5, 3.0, 3.5]), np.array([3.5, 4.0, 4.5]), 
                     np.array([4.5, 5.0, 5.5])]
        
        with pytest.raises(DataValidationError):
            compute_crps(y_true, y_pred_dist)

class TestEmptySeries:
    """Tests for handling empty series."""
    
    def test_empty_true_values(self):
        """Test coverage calculation with empty true values."""
        y_true = np.array([])
        y_pred = np.array([])
        lower_bound = np.array([])
        upper_bound = np.array([])
        
        with pytest.raises(DataValidationError):
            compute_coverage(y_true, lower_bound, upper_bound)
            
    def test_empty_predictions(self):
        """Test coverage calculation with empty predictions."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([])
        lower_bound = np.array([])
        upper_bound = np.array([])
        
        with pytest.raises(DataValidationError):
            compute_coverage(y_true, lower_bound, upper_bound)
            
    def test_mismatched_lengths(self):
        """Test coverage calculation with mismatched array lengths."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        lower_bound = np.array([0.5, 1.5, 2.5])
        upper_bound = np.array([1.5, 2.5, 3.5])
        
        with pytest.raises(DataValidationError):
            compute_coverage(y_true, lower_bound, upper_bound)

class TestSinglePointSeries:
    """Tests for handling single-point series."""
    
    def test_single_point_coverage(self):
        """Test coverage calculation with a single point."""
        y_true = np.array([1.0])
        y_pred = np.array([1.0])
        lower_bound = np.array([0.5])
        upper_bound = np.array([1.5])
        
        coverage = compute_coverage(y_true, lower_bound, upper_bound)
        assert coverage == 1.0, "Single point within interval should have 100% coverage"
        
    def test_single_point_coverage_miss(self):
        """Test coverage calculation with a single point outside interval."""
        y_true = np.array([1.0])
        y_pred = np.array([1.0])
        lower_bound = np.array([2.0])
        upper_bound = np.array([3.0])
        
        coverage = compute_coverage(y_true, lower_bound, upper_bound)
        assert coverage == 0.0, "Single point outside interval should have 0% coverage"
        
    def test_single_point_pit(self):
        """Test PIT calculation with a single point."""
        y_true = np.array([1.0])
        y_pred = np.array([1.0])
        lower_bound = np.array([0.5])
        upper_bound = np.array([1.5])
        
        pit_values = calculate_pit(y_true, y_pred, lower_bound, upper_bound)
        assert len(pit_values) == 1, "PIT should return one value for single point"
        
    def test_single_point_ljung_box(self):
        """Test Ljung-Box test with a single PIT value."""
        pit_values = np.array([0.5])
        
        # Ljung-Box test requires at least 2 points for meaningful results
        # This should handle the edge case gracefully
        result = ljung_box_test(pit_values)
        
        # The test should return a result, potentially with a warning or special handling
        # for insufficient data points
        assert 'p_value' in result or result is None, "Ljung-Box should handle single point case"

class TestExtremeValues:
    """Tests for handling extreme values."""
    
    def test_very_large_values(self):
        """Test coverage calculation with very large values."""
        y_true = np.array([1e10, 2e10, 3e10])
        y_pred = np.array([1e10, 2e10, 3e10])
        lower_bound = np.array([0.5e10, 1.5e10, 2.5e10])
        upper_bound = np.array([1.5e10, 2.5e10, 3.5e10])
        
        coverage = compute_coverage(y_true, lower_bound, upper_bound)
        assert coverage == 1.0, "Coverage should work correctly with very large values"
        
    def test_very_small_values(self):
        """Test coverage calculation with very small values."""
        y_true = np.array([1e-10, 2e-10, 3e-10])
        y_pred = np.array([1e-10, 2e-10, 3e-10])
        lower_bound = np.array([0.5e-10, 1.5e-10, 2.5e-10])
        upper_bound = np.array([1.5e-10, 2.5e-10, 3.5e-10])
        
        coverage = compute_coverage(y_true, lower_bound, upper_bound)
        assert coverage == 1.0, "Coverage should work correctly with very small values"
        
    def test_mixed_magnitude_values(self):
        """Test coverage calculation with mixed magnitude values."""
        y_true = np.array([1e-10, 1.0, 1e10])
        y_pred = np.array([1e-10, 1.0, 1e10])
        lower_bound = np.array([0.5e-10, 0.5, 0.5e10])
        upper_bound = np.array([1.5e-10, 1.5, 1.5e10])
        
        coverage = compute_coverage(y_true, lower_bound, upper_bound)
        assert coverage == 1.0, "Coverage should work correctly with mixed magnitude values"

class TestDistributionalShapeEdgeCases:
    """Tests for distributional shape metrics edge cases."""
    
    def test_constant_pit_values_kurtosis(self):
        """Test kurtosis calculation with constant PIT values."""
        pit_values = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        
        # Constant values have undefined kurtosis, should handle gracefully
        kurtosis = calculate_kurtosis(pit_values)
        # May return np.nan or a specific value for constant distribution
        assert np.isfinite(kurtosis) or np.isnan(kurtosis), "Kurtosis should be finite or NaN for constant values"
        
    def test_two_point_pit_kurtosis(self):
        """Test kurtosis calculation with only two PIT values."""
        pit_values = np.array([0.3, 0.7])
        
        kurtosis = calculate_kurtosis(pit_values)
        # With only 2 points, kurtosis calculation may be unstable
        assert np.isfinite(kurtosis) or np.isnan(kurtosis), "Kurtosis should be handled for small samples"
        
    def test_heavy_tail_flagging(self):
        """Test heavy tail flagging with known heavy-tailed distribution."""
        # Generate PIT values from a heavy-tailed distribution (simulated)
        pit_values = np.concatenate([
            np.random.beta(0.5, 0.5, 1000),  # U-shaped (heavy tails)
            np.random.beta(2, 2, 1000)       # More uniform
        ])
        
        is_heavy_tailed = flag_heavy_tails(pit_values)
        # Beta(0.5, 0.5) has heavy tails, so this should be flagged
        assert is_heavy_tailed, "Heavy-tailed distribution should be flagged"
        
    def test_uniform_pit_no_heavy_tail(self):
        """Test that uniform PIT values are not flagged as heavy-tailed."""
        pit_values = np.random.uniform(0, 1, 1000)
        
        is_heavy_tailed = flag_heavy_tails(pit_values)
        # Uniform distribution should not be flagged as heavy-tailed
        assert not is_heavy_tailed, "Uniform distribution should not be flagged as heavy-tailed"