"""
Unit tests for binomial test and Wilson confidence interval width.

This module verifies:
1. The binomial test implementation correctly computes p-values against scipy.stats.
2. The Wilson confidence interval width is <= 0.10 for sufficiently large sample sizes,
   adhering to the constraint in arXiv:1807.00365 regarding precision requirements.
"""
import pytest
import numpy as np
from scipy import stats
from code.src.audit.prevalence import binomial_test, wilson_ci, compute_prevalence
from code.src.config import set_rng_seed


class TestBinomialTest:
    """Tests for the binomial_test function."""

    def test_binomial_test_matches_scipy(self):
        """Verify our binomial test matches scipy.stats.binomtest for a standard case."""
        set_rng_seed(42)
        successes = 150
        n = 300
        p_null = 0.5

        # Calculate using our implementation
        p_val_our, ci_lower, ci_upper = binomial_test(successes, n, p_null)

        # Calculate using scipy
        result = stats.binomtest(successes, n, p_null)
        p_val_scipy = result.pvalue

        # Assert p-values are very close (allowing for minor floating point differences)
        assert np.isclose(p_val_our, p_val_scipy, atol=1e-6), \
            f"P-value mismatch: ours={p_val_our}, scipy={p_val_scipy}"

    def test_binomial_test_extreme_cases(self):
        """Test binomial test with extreme proportions (0 and 1)."""
        set_rng_seed(42)

        # Case 1: All successes
        p_val_1, _, _ = binomial_test(100, 100, 0.5)
        assert p_val_1 < 1e-10, "P-value should be extremely small for 100% success"

        # Case 2: No successes
        p_val_2, _, _ = binomial_test(0, 100, 0.5)
        assert p_val_2 < 1e-10, "P-value should be extremely small for 0% success"

        # Case 3: Exact null (p=0.5, n=100, k=50)
        p_val_3, _, _ = binomial_test(50, 100, 0.5)
        # For n=100, k=50, p=0.5, the two-sided p-value should be close to 1.0
        assert p_val_3 > 0.9, f"P-value for exact null should be high, got {p_val_3}"


class TestWilsonCI:
    """Tests for the Wilson confidence interval function."""

    def test_wilson_ci_width_constraint(self):
        """
        Verify that the Wilson CI width is <= 0.10 for sample sizes >= 300.
        This enforces the constraint from arXiv:1807.00365 regarding precision.
        """
        set_rng_seed(42)
        n = 300
        p_hat = 0.5
        alpha = 0.05

        lower, upper = wilson_ci(n, p_hat, alpha)
        width = upper - lower

        assert width <= 0.10, \
            f"CI width {width} exceeds 0.10 for n={n}. Constraint violation."

    def test_wilson_ci_width_varies_with_n(self):
        """Verify that CI width decreases as sample size increases."""
        set_rng_seed(42)
        p_hat = 0.5
        alpha = 0.05

        widths = []
        sample_sizes = [100, 300, 1000, 5000]

        for n in sample_sizes:
            lower, upper = wilson_ci(n, p_hat, alpha)
            widths.append(upper - lower)

        # Verify monotonic decrease
        for i in range(1, len(widths)):
            assert widths[i] < widths[i-1], \
                f"CI width should decrease as n increases: {widths[i-1]} -> {widths[i]}"

    def test_wilson_ci_symmetry(self):
        """Verify Wilson CI is symmetric around p_hat for p_hat = 0.5."""
        set_rng_seed(42)
        n = 1000
        p_hat = 0.5
        alpha = 0.05

        lower, upper = wilson_ci(n, p_hat, alpha)
        midpoint = (lower + upper) / 2

        assert np.isclose(midpoint, p_hat, atol=1e-6), \
            f"Wilson CI should be symmetric around 0.5. Midpoint: {midpoint}"

    def test_wilson_ci_bounds(self):
        """Verify Wilson CI bounds are within [0, 1]."""
        set_rng_seed(42)
        n = 50
        alpha = 0.05

        for p_hat in [0.01, 0.1, 0.5, 0.9, 0.99]:
            lower, upper = wilson_ci(n, p_hat, alpha)
            assert 0 <= lower <= 1, f"Lower bound {lower} out of [0, 1]"
            assert 0 <= upper <= 1, f"Upper bound {upper} out of [0, 1]"
            assert lower <= upper, f"Lower bound {lower} > Upper bound {upper}"


class TestComputePrevalence:
    """Tests for the compute_prevalence function."""

    def test_compute_prevalence_basic(self):
        """Test basic prevalence calculation."""
        set_rng_seed(42)
        inconsistent_count = 25
        total_count = 100

        prevalence, ci_lower, ci_upper = compute_prevalence(inconsistent_count, total_count)

        assert np.isclose(prevalence, 0.25, atol=1e-6), \
            f"Prevalence should be 0.25, got {prevalence}"
        assert ci_lower <= prevalence <= ci_upper, \
            f"Prevalence {prevalence} not within CI [{ci_lower}, {ci_upper}]"

    def test_compute_prevalence_zero_inconsistent(self):
        """Test prevalence calculation with zero inconsistent records."""
        set_rng_seed(42)
        prevalence, ci_lower, ci_upper = compute_prevalence(0, 100)

        assert np.isclose(prevalence, 0.0, atol=1e-6), \
            f"Prevalence should be 0.0, got {prevalence}"
        assert ci_lower >= 0.0, "Lower bound should be >= 0"
        assert ci_upper >= 0.0, "Upper bound should be >= 0"

    def test_compute_prevalence_all_inconsistent(self):
        """Test prevalence calculation with all records inconsistent."""
        set_rng_seed(42)
        prevalence, ci_lower, ci_upper = compute_prevalence(100, 100)

        assert np.isclose(prevalence, 1.0, atol=1e-6), \
            f"Prevalence should be 1.0, got {prevalence}"
        assert ci_lower <= 1.0, "Lower bound should be <= 1"
        assert ci_upper <= 1.0, "Upper bound should be <= 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
