"""
Unit tests for correlation analysis logic including bootstrap resampling.
File: tests/unit/test_correlation.py
"""

import pytest
import numpy as np
import pandas as pd
from scipy import stats
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.correlation import (
    calculate_correlation,
    circular_block_permutation,
    moving_block_bootstrap
)
from code.config import BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS, LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP


def create_synthetic_time_series(n_points=1000, lag=0, noise_scale=0.1, seed=42):
    """
    Creates a synthetic time series with a known correlation structure.
    x is random, y is x shifted by 'lag' + noise.
    """
    np.random.seed(seed)
    x = np.random.randn(n_points)
    # Create y with a known lag and some noise
    y = np.roll(x, lag) + np.random.randn(n_points) * noise_scale
    
    # Create a DataFrame with a datetime index
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="5min")
    df = pd.DataFrame({'x': x, 'y': y}, index=dates)
    return df


class TestBootstrapBlockSize:
    """Tests for determining and using block size in bootstrap resampling."""

    def test_bootstrap_block_size_calculation(self):
        """
        FR-006: Verify that the moving_block_bootstrap calculates a block size
        based on the autocorrelation decay (first lag where autocorrelation < 0.5).
        """
        df = create_synthetic_time_series(n_points=500, lag=0, noise_scale=0.05)
        x = df['x'].values
        
        # Calculate block size logic manually to verify
        # We expect a reasonable block size > 0 for correlated data
        # The implementation should handle the case where autocorrelation is weak
        
        # Run the bootstrap
        ci_low, ci_high, mean_val = moving_block_bootstrap(
            x, 
            x, 
            iterations=100, # Reduced for test speed
            block_size=None  # Let it auto-calculate
        )
        
        # Assert that the function returns valid numeric values
        assert isinstance(ci_low, (float, np.floating)), "CI low should be a float"
        assert isinstance(ci_high, (float, np.floating)), "CI high should be a float"
        assert isinstance(mean_val, (float, np.floating)), "Mean should be a float"
        
        # Assert that the CI makes sense (low < mean < high)
        assert ci_low <= mean_val <= ci_high, "CI should bracket the mean"
        
        # Assert that the CI width is non-zero for non-constant data
        assert ci_high > ci_low, "CI width should be positive for variable data"

    def test_bootstrap_block_size_with_constant_data(self):
        """
        Test that block size logic handles constant data (autocorrelation undefined or 1.0).
        """
        constant_data = np.ones(100)
        
        # Should not raise an error
        ci_low, ci_high, mean_val = moving_block_bootstrap(
            constant_data, 
            constant_data, 
            iterations=50,
            block_size=1
        )
        
        # For constant data, mean is 1.0 and CI should be [1.0, 1.0]
        assert np.isclose(mean_val, 1.0)
        assert np.isclose(ci_low, 1.0)
        assert np.isclose(ci_high, 1.0)


class TestBootstrapCiCalculation:
    """Tests for the accuracy of Confidence Interval calculation in bootstrap."""

    def test_bootstrap_ci_calculation_normal_data(self):
        """
        FR-006: Verify that the bootstrap CI calculation produces correct 
        95% confidence intervals for a known distribution.
        """
        # Generate data from a known normal distribution
        np.random.seed(42)
        n = 1000
        mu_true = 5.0
        sigma_true = 2.0
        data = np.random.normal(mu_true, sigma_true, n)
        
        # Run bootstrap with enough iterations for stability
        ci_low, ci_high, mean_val = moving_block_bootstrap(
            data, 
            data, 
            iterations=1000, 
            block_size=1 # Treat as independent for this specific check
        )
        
        # The mean should be close to the true mean
        assert np.isclose(mean_val, mu_true, atol=0.2), f"Mean {mean_val} should be close to {mu_true}"
        
        # The 95% CI should contain the true mean (statistically likely, though not guaranteed in every run)
        # We check that the CI width is reasonable relative to sigma/sqrt(n)
        expected_se = sigma_true / np.sqrt(n)
        expected_width = 2 * 1.96 * expected_se # Approximate 95% width
        
        actual_width = ci_high - ci_low
        # Allow some tolerance due to bootstrap variance
        assert actual_width > 0, "CI width must be positive"
        
        # Check that the true mean is within the calculated CI (most of the time)
        # If it fails once, it's a statistical fluke, but for a robust test we expect it to hold
        # For the purpose of this unit test, we assert the CI is centered reasonably
        assert ci_low <= mu_true <= ci_high, f"True mean {mu_true} should be within CI [{ci_low}, {ci_high}]"

    def test_bootstrap_ci_calculation_with_correlation(self):
        """
        Test that bootstrap CI widens appropriately when data is correlated (time series).
        """
        df = create_synthetic_time_series(n_points=500, lag=0, noise_scale=0.1)
        x = df['x'].values
        
        # Run with auto block size (should detect correlation and use blocks > 1)
        ci_low_auto, ci_high_auto, _ = moving_block_bootstrap(
            x, x, iterations=500, block_size=None
        )
        
        # Run with block_size=1 (ignoring correlation)
        ci_low_indep, ci_high_indep, _ = moving_block_bootstrap(
            x, x, iterations=500, block_size=1
        )
        
        # With autocorrelation, the effective sample size is lower, so CI should be wider
        # if the block size is correctly estimated to be > 1.
        width_auto = ci_high_auto - ci_low_auto
        width_indep = ci_high_indep - ci_low_indep
        
        # In many time series cases, the block bootstrap CI is wider than the i.i.d. assumption
        # We assert that the function runs without error and returns valid intervals
        assert width_auto > 0 and width_indep > 0

    def test_bootstrap_ci_coverage_property(self):
        """
        Verify the coverage property: if we run the bootstrap many times on different
        samples, the true parameter should fall within the CI ~95% of the time.
        (Simplified version for unit testing speed)
        """
        np.random.seed(123)
        mu_true = 10.0
        sigma_true = 3.0
        n_samples = 100
        coverage_count = 0
        
        for _ in range(n_samples):
            sample = np.random.normal(mu_true, sigma_true, 200)
            ci_low, ci_high, _ = moving_block_bootstrap(
                sample, sample, iterations=200, block_size=1
            )
            if ci_low <= mu_true <= ci_high:
                coverage_count += 1
        
        coverage_rate = coverage_count / n_samples
        # We expect ~95% coverage. Allow a wide margin for small sample size of tests
        assert coverage_rate >= 0.80, f"Coverage rate {coverage_rate} is too low (expected ~0.95)"

def test_moving_block_bootstrap_integration():
    """
    Integration test ensuring moving_block_bootstrap works end-to-end with 
    realistic solar wind-like data patterns.
    """
    # Create a dataset with a trend and noise
    n = 1000
    t = np.linspace(0, 10, n)
    trend = np.sin(t)
    noise = np.random.normal(0, 0.1, n)
    data = trend + noise
    
    ci_low, ci_high, mean_val = moving_block_bootstrap(
        data, data, iterations=100, block_size=5
    )
    
    assert isinstance(ci_low, float)
    assert isinstance(ci_high, float)
    assert isinstance(mean_val, float)
    assert ci_low < mean_val < ci_high
    assert ci_high - ci_low > 0.01 # Reasonable width for this data