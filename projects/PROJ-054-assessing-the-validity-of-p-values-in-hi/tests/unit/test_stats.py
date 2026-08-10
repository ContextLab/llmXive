"""
Unit tests for statistical analysis utilities.
Tests KS statistic calculation and bootstrap confidence intervals.
"""
import pytest
import numpy as np
import json
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analyze_pvalues import calculate_ks_statistic
from bootstrap_ci import calculate_bootstrap_ci


class TestKSStatistic:
    """Tests for KS statistic calculation."""

    def test_uniform_pvalues(self):
        """Test KS statistic on truly uniform p-values is small."""
        np.random.seed(42)
        n = 10000
        uniform_pvalues = np.random.uniform(0, 1, n)

        # Compare against uniform distribution
        ks_stat, p_val = calculate_ks_statistic(uniform_pvalues, reference_type="uniform")

        # For uniform vs uniform, KS should be small (< 0.02 for large n)
        assert ks_stat < 0.02, f"KS statistic {ks_stat:.4f} unexpectedly large for uniform data"

    def test_anti_conservative_pvalues(self):
        """Test KS statistic detects anti-conservative bias (excess small p-values)."""
        np.random.seed(123)
        n = 10000

        # Generate p-values that are anti-conservative (biased toward 0)
        # e.g., Beta(0.5, 1) distribution which has excess mass near 0
        anti_conservative = np.random.beta(0.5, 1, n)

        ks_stat, p_val = calculate_ks_statistic(anti_conservative, reference_type="uniform")

        # KS should be significantly larger than for uniform
        assert ks_stat > 0.05, f"KS statistic {ks_stat:.4f} too small to detect bias"

    def test_conservative_pvalues(self):
        """Test KS statistic detects conservative bias (excess large p-values)."""
        np.random.seed(456)
        n = 10000

        # Generate p-values that are conservative (biased toward 1)
        # e.g., Beta(1, 0.5) distribution which has excess mass near 1
        conservative = np.random.beta(1, 0.5, n)

        ks_stat, p_val = calculate_ks_statistic(conservative, reference_type="uniform")

        # KS should be significantly larger than for uniform
        assert ks_stat > 0.05, f"KS statistic {ks_stat:.4f} too small to detect bias"


class TestBootstrapCI:
    """Tests for bootstrap confidence interval calculation."""

    def test_bootstrap_ci_narrow_for_large_sample(self):
        """Test that bootstrap CI narrows with larger sample size."""
        np.random.seed(789)
        n_small = 100
        n_large = 10000

        # Generate uniform p-values
        small_sample = np.random.uniform(0, 1, n_small)
        large_sample = np.random.uniform(0, 1, n_large)

        ci_small = calculate_bootstrap_ci(small_sample, n_bootstrap=1000)
        ci_large = calculate_bootstrap_ci(large_sample, n_bootstrap=1000)

        # Width of CI should be smaller for larger sample
        width_small = ci_small["upper"] - ci_small["lower"]
        width_large = ci_large["upper"] - ci_large["lower"]

        assert width_large < width_small, \
            f"CI width should decrease with sample size: {width_large:.4f} vs {width_small:.4f}"

    def test_bootstrap_ci_contains_true_value(self):
        """Test that bootstrap CI contains the true KS statistic for uniform data."""
        np.random.seed(101)
        n = 5000
        uniform_pvalues = np.random.uniform(0, 1, n)

        # Calculate true KS statistic
        from scipy import stats
        true_ks, _ = stats.kstest(uniform_pvalues, 'uniform')

        # Calculate bootstrap CI
        ci = calculate_bootstrap_ci(uniform_pvalues, n_bootstrap=1000)

        # True KS should be within CI
        assert ci["lower"] <= true_ks <= ci["upper"], \
            f"True KS {true_ks:.4f} not in CI [{ci['lower']:.4f}, {ci['upper']:.4f}]"
