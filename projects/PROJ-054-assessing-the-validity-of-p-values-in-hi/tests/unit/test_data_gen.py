"""
Unit tests for data generation utilities in generate_data.py.
These tests verify correlation structure accuracy and distributional shape validation.
"""
import pytest
import numpy as np
from scipy import stats
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from generate_data import generate_correlated_data, generate_distribution_violations


class TestCorrelatedDataGeneration:
    """Tests for T012: Correlation matrix generation accuracy."""

    def test_no_correlation_identity(self):
        """Test that rho=0.0 produces near-identity correlation matrix."""
        n, p, rho = 100, 50, 0.0
        data = generate_correlated_data(n, p, rho, seed=42)

        # Calculate empirical correlation
        corr_matrix = np.corrcoef(data.T)

        # Diagonal should be 1.0
        np.testing.assert_array_almost_equal(
            np.diag(corr_matrix),
            np.ones(p),
            decimal=5,
            err_msg="Diagonal of correlation matrix should be 1.0"
        )

        # Off-diagonal should be near 0
        off_diag = corr_matrix[~np.eye(p, dtype=bool)]
        assert np.allclose(off_diag, 0.0, atol=0.1), \
            f"Off-diagonal correlations should be near 0, max observed: {np.max(np.abs(off_diag))}"

    def test_strong_positive_correlation(self):
        """Test that high rho produces strong positive correlations."""
        n, p, rho = 500, 50, 0.9
        data = generate_correlated_data(n, p, rho, seed=42)

        corr_matrix = np.corrcoef(data.T)
        off_diag = corr_matrix[~np.eye(p, dtype=bool)]

        # Average off-diagonal correlation should be close to rho
        mean_off_diag = np.mean(off_diag)
        assert abs(mean_off_diag - rho) < 0.1, \
            f"Mean off-diagonal correlation {mean_off_diag} should be close to {rho}"

    def test_deterministic_with_seed(self):
        """Test that same seed produces identical data."""
        n, p, rho = 100, 20, 0.5
        seed = 12345

        data1 = generate_correlated_data(n, p, rho, seed=seed)
        data2 = generate_correlated_data(n, p, rho, seed=seed)

        np.testing.assert_array_equal(data1, data2, err_msg="Same seed should produce identical data")


class TestDistributionViolations:
    """Tests for T013: Distribution shape validation."""

    def test_t_dist_df3(self):
        """Test that t-distribution with df=3 produces heavy tails (KS distance < 0.01)."""
        n = 10000
        dist_type = "t"
        params = {"df": 3}

        data = generate_distribution_violations(n, dist_type, params, seed=42)

        # KS test against theoretical t-distribution
        ks_stat, p_value = stats.kstest(data, 't', args=(params["df"],))

        # For large n, KS statistic should be small if distribution matches
        # Allow KS < 0.01 for df=3 (heavy-tailed)
        assert ks_stat < 0.01, \
            f"KS statistic {ks_stat:.4f} exceeds threshold 0.01 for t-dist df=3"

        # Verify heavy tails: kurtosis should be > 3 (normal has kurtosis 3)
        kurtosis = stats.kurtosis(data, fisher=False)
        assert kurtosis > 3, f"Kurtosis {kurtosis} should be > 3 for heavy-tailed t-dist"

    def test_skewed_normal(self):
        """Test that skewed normal produces asymmetry."""
        n = 10000
        dist_type = "skew_normal"
        params = {"a": 5}  # Skewness parameter

        data = generate_distribution_violations(n, dist_type, params, seed=42)

        # Check skewness
        skewness = stats.skew(data)
        assert abs(skewness - 1.0) < 0.5, \
            f"Skewness {skewness} should be positive for skewed normal (a=5)"

        # KS test against skewed normal
        ks_stat, p_value = stats.kstest(data, 'skewnorm', args=(params["a"],))
        assert ks_stat < 0.01, \
            f"KS statistic {ks_stat:.4f} exceeds threshold 0.01 for skew_normal"

    def test_uniform_control(self):
        """Test that uniform distribution (control) passes KS test."""
        n = 10000
        dist_type = "uniform"
        params = {}

        data = generate_distribution_violations(n, dist_type, params, seed=42)

        ks_stat, p_value = stats.kstest(data, 'uniform')
        assert ks_stat < 0.01, \
            f"KS statistic {ks_stat:.4f} exceeds threshold 0.01 for uniform"


class TestDataDimensions:
    """Tests for data shape and dimensionality."""

    def test_correct_dimensions(self):
        """Test that generated data has correct (n, p) shape."""
        test_cases = [
            (100, 1000),
            (50, 5000),
            (200, 100),
        ]

        for n, p in test_cases:
            data = generate_correlated_data(n, p, rho=0.5, seed=42)
            assert data.shape == (n, p), \
                f"Expected shape ({n}, {p}), got {data.shape}"

    def test_no_nan_values(self):
        """Test that generated data contains no NaN values."""
        data = generate_correlated_data(100, 100, rho=0.5, seed=42)
        assert not np.any(np.isnan(data)), "Generated data should not contain NaN values"

    def test_finite_values(self):
        """Test that all values are finite (no inf)."""
        data = generate_correlated_data(100, 100, rho=0.5, seed=42)
        assert np.all(np.isfinite(data)), "Generated data should contain only finite values"
