"""
Unit tests for data generation utilities.
Tests for code/generate_data.py
"""
import numpy as np
import pytest
from generate_data import generate_correlated_data, generate_distribution_violations


class TestCorrelatedDataGeneration:
    def test_no_correlation(self):
        """Test that rho=0.0 produces uncorrelated data."""
        n_samples, n_features = 100, 50
        data = generate_correlated_data(n_samples, n_features, rho=0.0, seed=42)

        assert data.shape == (n_samples, n_features)

        # Calculate correlation matrix
        corr_matrix = np.corrcoef(data.T)

        # Off-diagonal elements should be close to 0
        off_diag = corr_matrix[np.triu_indices(n_features, k=1)]
        assert np.mean(np.abs(off_diag)) < 0.1  # Allow some sampling noise

    def test_strong_correlation(self):
        """Test that rho=0.9 produces strongly correlated data."""
        n_samples, n_features = 100, 50
        data = generate_correlated_data(n_samples, n_features, rho=0.9, seed=42)

        assert data.shape == (n_samples, n_features)

        # Calculate correlation matrix
        corr_matrix = np.corrcoef(data.T)

        # Off-diagonal elements should be close to 0.9 on average
        off_diag = corr_matrix[np.triu_indices(n_features, k=1)]
        assert np.mean(off_diag) > 0.5  # Should be significantly positive

    def test_correlation_matrix_accuracy(self):
        """Test that generated data matches target correlation structure."""
        n_samples, n_features = 500, 20
        target_rho = 0.5
        data = generate_correlated_data(n_samples, n_features, rho=target_rho, seed=42)

        # Calculate empirical correlation
        corr_matrix = np.corrcoef(data.T)

        # Check diagonal is ~1
        assert np.allclose(np.diag(corr_matrix), 1.0, atol=0.01)

        # Check off-diagonals are close to target (with tolerance for sampling)
        off_diag = corr_matrix[np.triu_indices(n_features, k=1)]
        assert np.abs(np.mean(off_diag) - target_rho) < 0.1

    def test_different_sizes(self):
        """Test generation with different n and p values."""
        configs = [
            (50, 10),
            (100, 50),
            (200, 100),
            (500, 200)
        ]

        for n, p in configs:
            data = generate_correlated_data(n, p, rho=0.3, seed=42)
            assert data.shape == (n, p)

    def test_seed_reproducibility(self):
        """Test that same seed produces same results."""
        n_samples, n_features = 100, 50
        data1 = generate_correlated_data(n_samples, n_features, rho=0.5, seed=42)
        data2 = generate_correlated_data(n_samples, n_features, rho=0.5, seed=42)

        np.testing.assert_array_equal(data1, data2)

    def test_different_seeds_different_results(self):
        """Test that different seeds produce different results."""
        n_samples, n_features = 100, 50
        data1 = generate_correlated_data(n_samples, n_features, rho=0.5, seed=42)
        data2 = generate_correlated_data(n_samples, n_features, rho=0.5, seed=43)

        assert not np.array_equal(data1, data2)


class TestDistributionViolations:
    def test_t_distribution(self):
        """Test t-distribution generation with low degrees of freedom."""
        n_samples, n_features = 100, 50
        data = generate_distribution_violations(n_samples, n_features, dist_type="t", df=3)

        assert data.shape == (n_samples, n_features)

        # T-distribution with low df should have heavier tails
        # Check kurtosis is higher than normal (normal kurtosis = 3)
        kurtosis = np.mean([np.mean((data[:, i] - np.mean(data[:, i]))**4) /
                          (np.std(data[:, i])**4 + 1e-10) for i in range(n_features)])
        assert kurtosis > 3  # Should be heavier tailed

    def test_skewed_normal(self):
        """Test skewed normal distribution generation."""
        n_samples, n_features = 100, 50
        data = generate_distribution_violations(n_samples, n_features, dist_type="skew_normal", alpha=5)

        assert data.shape == (n_samples, n_features)

        # Check skewness is non-zero
        skewness = np.mean([np.mean((data[:, i] - np.mean(data[:, i]))**3) /
                         (np.std(data[:, i])**3 + 1e-10) for i in range(n_features)])
        assert np.abs(skewness) > 0.5  # Should be noticeably skewed

    def test_normal_distribution(self):
        """Test normal distribution generation (baseline)."""
        n_samples, n_features = 100, 50
        data = generate_distribution_violations(n_samples, n_features, dist_type="normal")

        assert data.shape == (n_samples, n_features)

        # Check skewness is near zero
        skewness = np.mean([np.mean((data[:, i] - np.mean(data[:, i]))**3) /
                         (np.std(data[:, i])**3 + 1e-10) for i in range(n_features)])
        assert np.abs(skewness) < 0.5

    def test_invalid_distribution_type(self):
        """Test that invalid distribution type raises error."""
        with pytest.raises(ValueError):
            generate_distribution_violations(100, 50, dist_type="invalid")

    def test_invalid_df_value(self):
        """Test that invalid df value raises error."""
        with pytest.raises(ValueError):
            generate_distribution_violations(100, 50, dist_type="t", df=-1)

    def test_t_dist_df3(self):
        """Test t-distribution with df=3 specifically (KS distance < 0.01)."""
        n_samples = 10000  # Large sample for accurate KS test
        n_features = 1
        data = generate_distribution_violations(n_samples, n_features, dist_type="t", df=3)

        # Flatten data
        sample_data = data.flatten()

        # Perform Kolmogorov-Smirnov test against theoretical t-distribution
        from scipy import stats
        ks_stat, p_value = stats.kstest(sample_data, 't', args=(3,))

        # KS statistic should be small for large sample
        assert ks_stat < 0.01, f"KS distance {ks_stat} exceeds 0.01 threshold"

    def test_seed_reproducibility_distributions(self):
        """Test that same seed produces same distribution results."""
        n_samples, n_features = 100, 50
        data1 = generate_distribution_violations(n_samples, n_features, dist_type="t", df=3, seed=42)
        data2 = generate_distribution_violations(n_samples, n_features, dist_type="t", df=3, seed=42)

        np.testing.assert_array_equal(data1, data2)

    def test_different_distributions_different_results(self):
        """Test that different distribution types produce different results."""
        n_samples, n_features = 100, 50
        data_normal = generate_distribution_violations(n_samples, n_features, dist_type="normal", seed=42)
        data_t = generate_distribution_violations(n_samples, n_features, dist_type="t", df=3, seed=42)

        # Distributions should be different
        assert not np.array_equal(data_normal, data_t)

    def test_combined_correlation_and_distribution(self):
        """Test combining correlation structure with distribution violations."""
        n_samples, n_features = 100, 50
        # First generate correlated normal data
        correlated_data = generate_correlated_data(n_samples, n_features, rho=0.5, seed=42)

        # Then apply distribution transformation
        transformed_data = generate_distribution_violations(
            n_samples, n_features,
            dist_type="t", df=3,
            seed=42,
            base_data=correlated_data
        )

        assert transformed_data.shape == (n_samples, n_features)

        # Should still have some correlation structure
        corr_matrix = np.corrcoef(transformed_data.T)
        off_diag = corr_matrix[np.triu_indices(n_features, k=1)]
        assert np.mean(off_diag) > 0.2  # Should retain some correlation
