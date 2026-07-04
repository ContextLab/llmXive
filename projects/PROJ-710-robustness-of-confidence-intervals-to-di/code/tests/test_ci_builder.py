"""
Unit tests for CI construction (percentile method) in code/analysis/ci_builder.py.

These tests verify that the CI builder correctly constructs confidence intervals
using the percentile bootstrap method, handles edge cases, and produces
deterministic results with fixed random seeds.
"""

import numpy as np
import pytest
import json
import os
from pathlib import Path

# Import the CI builder module (will be implemented in T012)
# For now, we test the interface and expected behavior
from code.analysis.ci_builder import (
    build_percentile_ci,
    compute_bootstrap_distribution,
    validate_bootstrap_params
)

# Fix random seed for reproducibility in tests
TEST_SEED = 42
np.random.seed(TEST_SEED)

# Test constants
SAMPLE_SIZE = 100
N_BOOTSTRAP = 1000
CONFIDENCE_LEVEL = 0.95


class TestBootstrapValidation:
    """Tests for bootstrap parameter validation."""
    
    def test_valid_parameters(self):
        """Test that valid parameters pass validation."""
        result = validate_bootstrap_params(
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            min_sample_size=10
        )
        assert result is True
        
    def test_invalid_n_bootstrap(self):
        """Test that invalid n_bootstrap raises error."""
        with pytest.raises(ValueError):
            validate_bootstrap_params(
                n_bootstrap=0,
                confidence_level=CONFIDENCE_LEVEL,
                min_sample_size=10
            )
        
        with pytest.raises(ValueError):
            validate_bootstrap_params(
                n_bootstrap=-100,
                confidence_level=CONFIDENCE_LEVEL,
                min_sample_size=10
            )
            
    def test_invalid_confidence_level(self):
        """Test that invalid confidence_level raises error."""
        with pytest.raises(ValueError):
            validate_bootstrap_params(
                n_bootstrap=N_BOOTSTRAP,
                confidence_level=0.0,
                min_sample_size=10
            )
        
        with pytest.raises(ValueError):
            validate_bootstrap_params(
                n_bootstrap=N_BOOTSTRAP,
                confidence_level=1.5,
                min_sample_size=10
            )
            
    def test_sample_size_too_small(self):
        """Test that sample size below minimum raises error."""
        with pytest.raises(ValueError):
            validate_bootstrap_params(
                n_bootstrap=N_BOOTSTRAP,
                confidence_level=CONFIDENCE_LEVEL,
                min_sample_size=200
            )

class TestPercentileCIConstruction:
    """Tests for percentile confidence interval construction."""
    
    def test_mean_ci_normal_distribution(self):
        """Test CI construction for mean of normal distribution."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=10.0, scale=2.0, size=SAMPLE_SIZE)
        
        ci = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        # CI should contain the true mean (10.0) with high probability
        assert ci['lower'] < 10.0 < ci['upper']
        assert ci['point_estimate'] == np.mean(data)
        assert ci['confidence_level'] == CONFIDENCE_LEVEL
        
    def test_variance_ci_normal_distribution(self):
        """Test CI construction for variance of normal distribution."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=0.0, scale=3.0, size=SAMPLE_SIZE)
        
        ci = build_percentile_ci(
            data=data,
            statistic_func=np.var,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        # CI should contain the true variance (9.0) with high probability
        assert ci['lower'] < 9.0 < ci['upper']
        assert ci['point_estimate'] == np.var(data)
        
    def test_regression_coefficient_ci(self):
        """Test CI construction for regression coefficients."""
        np.random.seed(TEST_SEED)
        n_samples = 200
        X = np.random.normal(0, 1, (n_samples, 2))
        true_beta = np.array([2.5, -1.5])
        noise = np.random.normal(0, 0.5, n_samples)
        y = X @ true_beta + noise
        
        def regression_slope(data_X, data_y, coefficient_idx):
            """Fit OLS and return specific coefficient."""
            X_design = np.column_stack([np.ones(len(data_y)), data_X])
            try:
                beta_hat = np.linalg.lstsq(X_design, data_y, rcond=None)[0]
                return beta_hat[coefficient_idx + 1]  # Skip intercept
            except np.linalg.LinAlgError:
                return np.nan
        
        # Test for first coefficient
        ci = build_percentile_ci(
            data=(X, y),
            statistic_func=lambda d: regression_slope(d[0], d[1], 0),
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        # CI should contain the true coefficient (2.5)
        assert ci['lower'] < 2.5 < ci['upper']
        
    def test_deterministic_with_seed(self):
        """Test that CI construction is deterministic with fixed seed."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=5.0, scale=1.0, size=SAMPLE_SIZE)
        
        ci1 = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        ci2 = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        assert ci1['lower'] == ci2['lower']
        assert ci1['upper'] == ci2['upper']
        assert ci1['point_estimate'] == ci2['point_estimate']
        
    def test_different_confidence_levels(self):
        """Test CI construction with different confidence levels."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=10.0, scale=2.0, size=SAMPLE_SIZE)
        
        ci_90 = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=0.90,
            random_seed=TEST_SEED
        )
        
        ci_95 = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=0.95,
            random_seed=TEST_SEED
        )
        
        ci_99 = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=0.99,
            random_seed=TEST_SEED
        )
        
        # Higher confidence level should produce wider intervals
        width_90 = ci_90['upper'] - ci_90['lower']
        width_95 = ci_95['upper'] - ci_95['lower']
        width_99 = ci_99['upper'] - ci_99['lower']
        
        assert width_90 < width_95 < width_99
        
    def test_small_sample_size(self):
        """Test CI construction with small sample size."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=10.0, scale=2.0, size=20)
        
        ci = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        assert ci['lower'] < ci['upper']
        assert not np.isnan(ci['point_estimate'])
        
    def test_large_sample_size(self):
        """Test CI construction with large sample size."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=10.0, scale=2.0, size=10000)
        
        ci = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        # CI should be very tight for large sample
        width = ci['upper'] - ci['lower']
        assert width < 0.1  # Should be very small
        
    def test_skewed_distribution(self):
        """Test CI construction for skewed distribution."""
        np.random.seed(TEST_SEED)
        # Exponential distribution (highly skewed)
        data = np.random.exponential(scale=2.0, size=SAMPLE_SIZE)
        
        ci = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        # True mean of exponential is scale parameter (2.0)
        # CI should contain 2.0 with high probability
        assert ci['lower'] < 2.0 < ci['upper']
        
    def test_outlier_robustness(self):
        """Test CI construction with outliers."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=10.0, scale=2.0, size=SAMPLE_SIZE)
        # Add extreme outliers
        data[0] = 1000.0
        data[-1] = -1000.0
        
        ci = build_percentile_ci(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        # CI should be wide due to outliers
        width = ci['upper'] - ci['lower']
        assert width > 10.0  # Should be significantly wider than without outliers
        
    def test_median_statistic(self):
        """Test CI construction for median statistic."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=10.0, scale=2.0, size=SAMPLE_SIZE)
        
        ci = build_percentile_ci(
            data=data,
            statistic_func=np.median,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        # CI should contain the true median (approximately 10.0)
        assert ci['lower'] < 10.0 < ci['upper']
        
    def test_custom_statistic(self):
        """Test CI construction with custom statistic function."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=10.0, scale=2.0, size=SAMPLE_SIZE)
        
        # Custom statistic: mean of top 25%
        def top_quartile_mean(x):
            sorted_x = np.sort(x)
            quartile_idx = int(len(x) * 0.75)
            return np.mean(sorted_x[quartile_idx:])
        
        ci = build_percentile_ci(
            data=data,
            statistic_func=top_quartile_mean,
            n_bootstrap=N_BOOTSTRAP,
            confidence_level=CONFIDENCE_LEVEL,
            random_seed=TEST_SEED
        )
        
        assert ci['lower'] < ci['upper']
        assert not np.isnan(ci['point_estimate'])

class TestBootstrapDistribution:
    """Tests for bootstrap distribution computation."""
    
    def test_bootstrap_distribution_shape(self):
        """Test that bootstrap distribution has correct shape."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=10.0, scale=2.0, size=SAMPLE_SIZE)
        
        bootstrap_dist = compute_bootstrap_distribution(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            random_seed=TEST_SEED
        )
        
        assert len(bootstrap_dist) == N_BOOTSTRAP
        assert not np.any(np.isnan(bootstrap_dist))
        
    def test_bootstrap_distribution_central_tendency(self):
        """Test that bootstrap distribution is centered near sample statistic."""
        np.random.seed(TEST_SEED)
        data = np.random.normal(loc=10.0, scale=2.0, size=SAMPLE_SIZE)
        
        sample_stat = np.mean(data)
        bootstrap_dist = compute_bootstrap_distribution(
            data=data,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            random_seed=TEST_SEED
        )
        
        bootstrap_mean = np.mean(bootstrap_dist)
        # Bootstrap mean should be close to sample statistic
        assert abs(bootstrap_mean - sample_stat) < 0.5
        
    def test_bootstrap_distribution_variance(self):
        """Test that bootstrap distribution variance decreases with sample size."""
        np.random.seed(TEST_SEED)
        
        # Small sample
        data_small = np.random.normal(loc=10.0, scale=2.0, size=20)
        bootstrap_small = compute_bootstrap_distribution(
            data=data_small,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            random_seed=TEST_SEED
        )
        
        # Large sample
        data_large = np.random.normal(loc=10.0, scale=2.0, size=1000)
        bootstrap_large = compute_bootstrap_distribution(
            data=data_large,
            statistic_func=np.mean,
            n_bootstrap=N_BOOTSTRAP,
            random_seed=TEST_SEED
        )
        
        var_small = np.var(bootstrap_small)
        var_large = np.var(bootstrap_large)
        
        # Variance should be smaller for larger sample
        assert var_small > var_large