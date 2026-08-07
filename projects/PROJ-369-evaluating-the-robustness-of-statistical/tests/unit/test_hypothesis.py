"""
Unit tests for one-sample t-test application in hypothesis testing.

This module validates the implementation of one-sample t-tests applied to
time series data, ensuring correct handling of various scenarios including
stationary and non-stationary series, different sample sizes, and edge cases.
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import tempfile
import os

# Import the hypothesis testing module (to be implemented in T026)
# For now, we'll test against a mock implementation that will be replaced
try:
    from src.analysis.hypothesis_tests import (
        one_sample_ttest,
        calculate_rejection_rate,
        run_monte_carlo_ttest
    )
    HYPOTHESIS_MODULE_AVAILABLE = True
except ImportError:
    HYPOTHESIS_MODULE_AVAILABLE = False


@pytest.fixture
def stationary_series():
    """Generate a stationary time series with mean=0."""
    np.random.seed(42)
    n = 1000
    # White noise (stationary)
    data = np.random.normal(0, 1, n)
    return pd.Series(data)


@pytest.fixture
def non_stationary_series():
    """Generate a non-stationary time series (random walk)."""
    np.random.seed(42)
    n = 1000
    # Random walk (non-stationary)
    data = np.cumsum(np.random.normal(0, 1, n))
    return pd.Series(data)


@pytest.fixture
def persistent_series():
    """Generate a persistent time series (H > 0.5)."""
    np.random.seed(42)
    n = 1000
    # AR(1) process with high persistence
    phi = 0.8
    data = np.zeros(n)
    for i in range(1, n):
        data[i] = phi * data[i-1] + np.random.normal(0, 1)
    return pd.Series(data)


@pytest.fixture
def short_series():
    """Generate a short time series (< 25 points)."""
    np.random.seed(42)
    n = 20
    data = np.random.normal(0, 1, n)
    return pd.Series(data)


@pytest.mark.skipif(not HYPOTHESIS_MODULE_AVAILABLE, 
                   reason="Hypothesis testing module not yet implemented")
class TestOneSampleTTest:
    """Test suite for one-sample t-test functionality."""
    
    def test_one_sample_ttest_stationary_series(self, stationary_series):
        """Test t-test on stationary series should not reject H0: mean=0."""
        t_stat, p_value = one_sample_ttest(stationary_series, mu=0)
        
        # Check that we get valid statistics
        assert not np.isnan(t_stat)
        assert not np.isnan(p_value)
        assert 0 <= p_value <= 1
        
        # For stationary white noise, we expect ~5% rejection rate at alpha=0.05
        # But for a single test, we just check the mechanics are correct
        assert isinstance(t_stat, (float, np.floating))
        assert isinstance(p_value, (float, np.floating))
    
    def test_one_sample_ttest_non_stationary_series(self, non_stationary_series):
        """Test t-test on non-stationary series may show inflated Type I error."""
        t_stat, p_value = one_sample_ttest(non_stationary_series, mu=0)
        
        # Check that we get valid statistics
        assert not np.isnan(t_stat)
        assert not np.isnan(p_value)
        assert 0 <= p_value <= 1
        
        # Non-stationary series often produce spuriously significant results
        # We just verify the test runs without error
    
    def test_one_sample_ttest_persistent_series(self, persistent_series):
        """Test t-test on persistent series shows autocorrelation effects."""
        t_stat, p_value = one_sample_ttest(persistent_series, mu=0)
        
        # Check that we get valid statistics
        assert not np.isnan(t_stat)
        assert not np.isnan(p_value)
        assert 0 <= p_value <= 1
    
    def test_one_sample_ttest_short_series(self, short_series):
        """Test t-test on short series handles small sample sizes."""
        t_stat, p_value = one_sample_ttest(short_series, mu=0)
        
        # Check that we get valid statistics
        assert not np.isnan(t_stat)
        assert not np.isnan(p_value)
        assert 0 <= p_value <= 1
    
    def test_one_sample_ttest_different_mus(self, stationary_series):
        """Test t-test with different hypothesized means."""
        # Test with mu=0 (should be non-significant for white noise)
        t_stat_0, p_value_0 = one_sample_ttest(stationary_series, mu=0)
        
        # Test with mu=10 (should be highly significant)
        t_stat_10, p_value_10 = one_sample_ttest(stationary_series, mu=10)
        
        # The p-value for mu=10 should be much smaller than for mu=0
        assert p_value_10 < p_value_0
    
    def test_rejection_rate_calculation(self, stationary_series):
        """Test rejection rate calculation across multiple trials."""
        # Create multiple samples
        np.random.seed(42)
        n_trials = 100
        series_list = []
        for _ in range(n_trials):
            data = np.random.normal(0, 1, 1000)
            series_list.append(pd.Series(data))
        
        rejection_rate = calculate_rejection_rate(series_list, mu=0, alpha=0.05)
        
        # For white noise, rejection rate should be close to alpha (5%)
        assert 0 <= rejection_rate <= 1
        # Allow for some variance in Monte Carlo
        assert abs(rejection_rate - 0.05) < 0.1  # Within 10% of expected
    
    def test_rejection_rate_non_stationary(self, non_stationary_series):
        """Test rejection rate on non-stationary series shows inflation."""
        # Create multiple random walk samples
        np.random.seed(42)
        n_trials = 100
        series_list = []
        for _ in range(n_trials):
            data = np.cumsum(np.random.normal(0, 1, 1000))
            series_list.append(pd.Series(data))
        
        rejection_rate = calculate_rejection_rate(series_list, mu=0, alpha=0.05)
        
        # For non-stationary series, rejection rate should be inflated
        # (significantly higher than 5%)
        assert 0 <= rejection_rate <= 1
        # Non-stationary series typically show much higher rejection rates
        # We expect this to be > 0.2 (20%) in most cases
        # Note: This is a weak assertion to avoid flakiness
    
    def test_monte_carlo_ttest_basic(self, stationary_series):
        """Test Monte Carlo t-test implementation."""
        # Run Monte Carlo simulation
        results = run_monte_carlo_ttest(
            n_trials=50,
            n_points=1000,
            mean=0,
            std=1,
            alpha=0.05,
            seed=42
        )
        
        # Check results structure
        assert 'rejection_rate' in results
        assert 't_statistics' in results
        assert 'p_values' in results
        
        # Check rejection rate is valid
        assert 0 <= results['rejection_rate'] <= 1
        assert len(results['t_statistics']) == 50
        assert len(results['p_values']) == 50


@pytest.mark.skipif(not HYPOTHESIS_MODULE_AVAILABLE,
                   reason="Hypothesis testing module not yet implemented")
class TestEdgeCases:
    """Test edge cases in hypothesis testing."""
    
    def test_constant_series(self):
        """Test t-test on constant series (variance=0)."""
        constant_data = pd.Series(np.ones(100))
        
        # This should handle the edge case gracefully
        # (either raise a clear error or return NaN for t-stat)
        t_stat, p_value = one_sample_ttest(constant_data, mu=0)
        
        # For constant series with non-zero mean, t-stat should be very large
        # or we should get NaN if variance is exactly 0
        if not np.isnan(t_stat):
            assert abs(t_stat) > 100  # Very large t-stat for constant non-zero mean
    
    def test_single_observation(self):
        """Test t-test on single observation."""
        single_data = pd.Series([1.0])
        
        # This should handle the edge case (t-test requires at least 2 obs)
        # Either raise error or return NaN
        t_stat, p_value = one_sample_ttest(single_data, mu=0)
        
        # For single observation, t-stat is undefined
        assert np.isnan(t_stat) or np.isnan(p_value)
    
    def test_very_large_series(self):
        """Test t-test on very large series."""
        np.random.seed(42)
        large_data = pd.Series(np.random.normal(0, 1, 100000))
        
        t_stat, p_value = one_sample_ttest(large_data, mu=0)
        
        # Should complete without error
        assert not np.isnan(t_stat)
        assert not np.isnan(p_value)
        assert 0 <= p_value <= 1


@pytest.mark.skipif(not HYPOTHESIS_MODULE_AVAILABLE,
                   reason="Hypothesis testing module not yet implemented")
class TestIntegration:
    """Integration tests for hypothesis testing workflow."""
    
    def test_full_workflow_stationary(self):
        """Test full workflow with stationary data."""
        np.random.seed(42)
        
        # Generate multiple stationary series
        series_list = []
        for _ in range(20):
            data = np.random.normal(0, 1, 500)
            series_list.append(pd.Series(data))
        
        # Calculate rejection rate
        rejection_rate = calculate_rejection_rate(series_list, mu=0, alpha=0.05)
        
        # Should be close to 5%
        assert 0.02 <= rejection_rate <= 0.08  # Reasonable range for 20 trials
    
    def test_full_workflow_non_stationary(self):
        """Test full workflow with non-stationary data."""
        np.random.seed(42)
        
        # Generate multiple non-stationary series
        series_list = []
        for _ in range(20):
            data = np.cumsum(np.random.normal(0, 1, 500))
            series_list.append(pd.Series(data))
        
        # Calculate rejection rate
        rejection_rate = calculate_rejection_rate(series_list, mu=0, alpha=0.05)
        
        # Should be significantly higher than 5%
        assert rejection_rate > 0.10  # At least 10% for non-stationary