"""
Unit tests for binomial test and Wilson CI width constraints.

Tests verify:
1. binomial_test() returns valid p-values for known inputs.
2. wilson_ci() returns intervals with width <= 0.10 for sufficient sample sizes.
3. Edge cases (0 successes, n successes) are handled correctly.
"""
import pytest
import math
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.prevalence import binomial_test, wilson_ci, compute_prevalence
from code.src.config import set_rng_seed


class TestBinomialTest:
    """Tests for the binomial_test function."""

    def test_binomial_test_known_values(self):
        """Test binomial test against known statistical values."""
        # n=100, k=50, p0=0.5 -> p-value should be ~1.0 (exact match)
        p_val = binomial_test(n=100, k=50, p0=0.5)
        assert 0.9 < p_val <= 1.0, f"Expected p-value near 1.0, got {p_val}"

        # n=100, k=60, p0=0.5 -> should be significant (two-tailed)
        p_val = binomial_test(n=100, k=60, p0=0.5)
        assert p_val < 0.05, f"Expected p-value < 0.05, got {p_val}"

    def test_binomial_test_edge_cases(self):
        """Test edge cases: 0 successes and n successes."""
        # All successes
        p_val = binomial_test(n=100, k=100, p0=0.5)
        assert p_val == 0.0 or p_val < 1e-10, f"Expected near 0 for all successes, got {p_val}"

        # No successes
        p_val = binomial_test(n=100, k=0, p0=0.5)
        assert p_val == 0.0 or p_val < 1e-10, f"Expected near 0 for no successes, got {p_val}"

    def test_binomial_test_invalid_inputs(self):
        """Test that invalid inputs raise appropriate errors."""
        with pytest.raises(ValueError):
            binomial_test(n=100, k=101, p0=0.5)  # k > n

        with pytest.raises(ValueError):
            binomial_test(n=100, k=-1, p0=0.5)  # k < 0

        with pytest.raises(ValueError):
            binomial_test(n=100, k=50, p0=1.5)  # p0 > 1


class TestWilsonCI:
    """Tests for the Wilson score confidence interval."""

    def test_wilson_ci_width_constraint(self):
        """Verify CI width is <= 0.10 for sufficient sample sizes."""
        # For p=0.5, n=100, alpha=0.05, width should be approx 0.10
        # Width = upper - lower
        lower, upper = wilson_ci(n=100, k=50, alpha=0.05)
        width = upper - lower
        assert width <= 0.10, f"Expected width <= 0.10, got {width:.4f}"

        # Larger sample size should yield narrower CI
        lower, upper = wilson_ci(n=400, k=200, alpha=0.05)
        width = upper - lower
        assert width <= 0.05, f"Expected width <= 0.05 for n=400, got {width:.4f}"

    def test_wilson_ci_symmetry(self):
        """Test that CI is symmetric around the proportion for p=0.5."""
        lower, upper = wilson_ci(n=100, k=50, alpha=0.05)
        mid = (lower + upper) / 2
        assert abs(mid - 0.5) < 1e-6, f"Expected midpoint near 0.5, got {mid}"

    def test_wilson_ci_edge_cases(self):
        """Test edge cases for Wilson CI."""
        # All successes
        lower, upper = wilson_ci(n=100, k=100, alpha=0.05)
        assert lower > 0.9, f"Expected lower bound > 0.9 for all successes, got {lower}"
        assert upper <= 1.0, f"Expected upper bound <= 1.0, got {upper}"

        # No successes
        lower, upper = wilson_ci(n=100, k=0, alpha=0.05)
        assert lower >= 0.0, f"Expected lower bound >= 0.0, got {lower}"
        assert upper < 0.1, f"Expected upper bound < 0.1 for no successes, got {upper}"

    def test_wilson_ci_invalid_inputs(self):
        """Test that invalid inputs raise appropriate errors."""
        with pytest.raises(ValueError):
            wilson_ci(n=100, k=101, alpha=0.05)  # k > n

        with pytest.raises(ValueError):
            wilson_ci(n=100, k=-1, alpha=0.05)  # k < 0

        with pytest.raises(ValueError):
            wilson_ci(n=100, k=50, alpha=1.5)  # alpha > 1


class TestComputePrevalence:
    """Tests for the compute_prevalence function."""

    def test_compute_prevalence_basic(self):
        """Test basic prevalence computation."""
        # 50 successes out of 100 -> prevalence = 0.5
        prev = compute_prevalence(n=100, k=50)
        assert abs(prev - 0.5) < 1e-10, f"Expected prevalence 0.5, got {prev}"

    def test_compute_prevalence_edge_cases(self):
        """Test edge cases for prevalence."""
        # All successes
        prev = compute_prevalence(n=100, k=100)
        assert prev == 1.0, f"Expected prevalence 1.0, got {prev}"

        # No successes
        prev = compute_prevalence(n=100, k=0)
        assert prev == 0.0, f"Expected prevalence 0.0, got {prev}"

    def test_compute_prevalence_invalid_inputs(self):
        """Test that invalid inputs raise appropriate errors."""
        with pytest.raises(ValueError):
            compute_prevalence(n=100, k=101)  # k > n

        with pytest.raises(ValueError):
            compute_prevalence(n=0, k=0)  # n = 0


class TestCIWidthConstraintIntegration:
    """Integration tests ensuring CI width constraints are met across various scenarios."""

    def test_ci_width_for_different_proportions(self):
        """Test CI width constraint for various proportions with n=200."""
        n = 200
        target_width = 0.10

        # Test proportions from 0.1 to 0.9
        for k in range(20, 181, 20):
            lower, upper = wilson_ci(n=n, k=k, alpha=0.05)
            width = upper - lower
            assert width <= target_width, (
                f"CI width constraint violated for k={k}, n={n}: "
                f"width={width:.4f} > {target_width}"
            )

    def test_minimum_n_for_target_width(self):
        """Determine minimum n required to achieve CI width <= 0.10."""
        target_width = 0.10
        p = 0.5  # Worst case for width
        
        # Binary search for minimum n
        low, high = 50, 500
        min_n = high
        
        while low <= high:
            mid = (low + high) // 2
            lower, upper = wilson_ci(n=mid, k=int(mid * p), alpha=0.05)
            width = upper - lower
            
            if width <= target_width:
                min_n = mid
                high = mid - 1
            else:
                low = mid + 1
        
        # Verify the found minimum n actually satisfies the constraint
        lower, upper = wilson_ci(n=min_n, k=int(min_n * p), alpha=0.05)
        assert (upper - lower) <= target_width, f"Minimum n={min_n} does not satisfy constraint"
        
        # Verify n-1 does not satisfy
        if min_n > 50:
            lower, upper = wilson_ci(n=min_n-1, k=int((min_n-1) * p), alpha=0.05)
            assert (upper - lower) > target_width, f"n={min_n-1} should not satisfy constraint"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])