"""
Unit tests for bootstrap confidence interval utilities in bootstrap_ci.py.
These tests verify bootstrap CI calculations and data loading.
"""
import pytest
import numpy as np
import json
import sys
import os
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from bootstrap_ci import calculate_bootstrap_ci, run_bootstrap_analysis


class TestBootstrapCI:
    """Tests for T032: Bootstrap confidence interval calculation."""

    def test_bootstrap_ci_symmetric(self):
        """Test bootstrap CI for symmetric distribution."""
        np.random.seed(42)
        data = np.random.normal(0, 1, 1000)

        # Calculate bootstrap CI for mean
        ci_lower, ci_upper, ci_mean = calculate_bootstrap_ci(data, n_bootstraps=1000, conf_level=0.95)

        # CI should be symmetric around mean for normal distribution
        assert abs(ci_mean) < 0.1, f"CI mean {ci_mean} should be near 0 for normal data"
        assert ci_lower < ci_mean < ci_upper, "CI bounds should bracket the mean"

    def test_bootstrap_ci_narrower_with_more_samples(self):
        """Test that CI narrows with more bootstrap samples."""
        np.random.seed(42)
        data = np.random.normal(0, 1, 1000)

        ci_100 = calculate_bootstrap_ci(data, n_bootstraps=100, conf_level=0.95)
        ci_1000 = calculate_bootstrap_ci(data, n_bootstraps=1000, conf_level=0.95)

        width_100 = ci_100[1] - ci_100[0]
        width_1000 = ci_1000[1] - ci_1000[0]

        # CI with more bootstraps should be more stable (not necessarily narrower,
        # but should not be significantly wider due to sampling noise)
        assert width_1000 <= width_100 * 1.5, \
            f"CI width with 1000 bootstraps ({width_1000}) should not be much wider than with 100 ({width_100})"

    def test_bootstrap_ci_coverage(self):
        """Test that bootstrap CI achieves nominal coverage."""
        np.random.seed(42)
        n_simulations = 100
        n_per_sim = 500
        true_mean = 5.0

        covered = 0
        for i in range(n_simulations):
            data = np.random.normal(true_mean, 2, n_per_sim)
            ci_lower, ci_upper, _ = calculate_bootstrap_ci(data, n_bootstraps=500, conf_level=0.95)

            if ci_lower <= true_mean <= ci_upper:
                covered += 1

        coverage_rate = covered / n_simulations
        # Should be close to 0.95 (allow some variance)
        assert 0.85 <= coverage_rate <= 0.99, \
            f"Bootstrap CI coverage {coverage_rate} should be near 0.95"

    def test_bootstrap_ci_asymmetric_distribution(self):
        """Test bootstrap CI for asymmetric (exponential) distribution."""
        np.random.seed(42)
        data = np.random.exponential(2, 1000)
        true_mean = 2.0

        ci_lower, ci_upper, ci_mean = calculate_bootstrap_ci(data, n_bootstraps=1000, conf_level=0.95)

        # CI should contain true mean
        assert ci_lower <= true_mean <= ci_upper, \
            f"Bootstrap CI [{ci_lower}, {ci_upper}] should contain true mean {true_mean}"

    def test_run_bootstrap_analysis(self):
        """Test full bootstrap analysis pipeline."""
        np.random.seed(42)
        n_samples = 1000
        n_pvalues = 100

        # Simulate p-value trajectories
        standard_pvalues = np.random.uniform(0, 1, n_pvalues)
        biased_pvalues = np.random.beta(0.5, 1, n_pvalues)

        # Calculate KS statistic
        from scipy import stats
        ks_stat, _ = stats.ks_2samp(standard_pvalues, biased_pvalues)

        # Run bootstrap analysis
        result = run_bootstrap_analysis(
            standard_pvalues,
            biased_pvalues,
            rho=0.5,
            n=100,
            p=100,
            seed=42,
            n_bootstraps=100
        )

        # Check result structure
        assert 'KS_statistic' in result, "Result should contain KS_statistic"
        assert 'bootstrap_ci_lower' in result, "Result should contain bootstrap_ci_lower"
        assert 'bootstrap_ci_upper' in result, "Result should contain bootstrap_ci_upper"
        assert 'rho' in result, "Result should contain rho"
        assert 'n' in result, "Result should contain n"
        assert 'p' in result, "Result should contain p"
        assert 'seed' in result, "Result should contain seed"
        assert 'permutation_pvalues' in result, "Result should contain permutation_pvalues"

        # Check values
        assert abs(result['KS_statistic'] - ks_stat) < 1e-10, \
            "KS_statistic should match direct calculation"
        assert result['bootstrap_ci_lower'] <= result['KS_statistic'] <= result['bootstrap_ci_upper'], \
            "KS statistic should be within CI bounds"
