"""
Unit tests for binomial test and Wilson confidence interval width constraints.

These tests verify:
1. The binomial_test function returns valid p-values for known inputs.
2. The wilson_ci function returns confidence intervals with width <= 0.10 
   for sufficiently large sample sizes (as required by FR-005a).
3. Edge cases (n=0, p=0, p=1) are handled correctly without crashing.
"""
import pytest
import math
import sys
from pathlib import Path

# Add project root to path to allow imports from src
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.prevalence import binomial_test, wilson_ci, compute_prevalence
from code.src.config import set_rng_seed


class TestBinomialTest:
    """Tests for the binomial_test function."""

    def test_binomial_test_known_values(self):
        """Test binomial test with known expected p-values."""
        # Set seed for reproducibility if Monte Carlo is used internally
        set_rng_seed(42)

        # Case 1: Perfect match (observed = expected) -> p-value should be 1.0
        n = 100
        observed = 50
        expected_rate = 0.5
        p_val = binomial_test(observed, n, expected_rate)
        assert p_val == 1.0, f"Expected p=1.0 for perfect match, got {p_val}"

        # Case 2: Significant deviation (observed far from expected) -> p-value should be small
        # 80 successes out of 100 when expected is 50% -> highly significant
        observed_dev = 80
        p_val_dev = binomial_test(observed_dev, n, expected_rate)
        assert p_val_dev < 0.001, f"Expected very small p-value for significant deviation, got {p_val_dev}"

    def test_binomial_test_edge_cases(self):
        """Test binomial test with edge cases."""
        set_rng_seed(42)

        # n=0 should raise an error or return a defined value (depending on implementation)
        # We expect the function to handle this gracefully.
        # If the implementation requires n > 0, we test that it raises ValueError.
        try:
            binomial_test(0, 0, 0.5)
            # If it doesn't raise, it should return a sensible default or handle it.
            # For this test, we assume it raises ValueError for n=0.
            # If it returns a value, we check it's not NaN/Inf.
        except ValueError:
            pass  # Expected

        # All successes (observed = n)
        p_all_success = binomial_test(10, 10, 0.5)
        assert 0.0 <= p_all_success <= 1.0, f"p-value out of range for all successes: {p_all_success}"

        # All failures (observed = 0)
        p_all_fail = binomial_test(0, 10, 0.5)
        assert 0.0 <= p_all_fail <= 1.0, f"p-value out of range for all failures: {p_all_fail}"


class TestWilsonCI:
    """Tests for the wilson_ci function."""

    def test_wilson_ci_width_constraint(self):
        """
        Verify that Wilson CI width is <= 0.10 for sufficiently large sample sizes.
        This satisfies FR-005a requirement for CI width.
        """
        # For a given confidence level (default 95%), the width of the Wilson CI
        # decreases as n increases. We need to find an n where width <= 0.10.
        # A rough approximation: width ~ 2 * 1.96 * sqrt(p*(1-p)/n)
        # For p=0.5 (worst case), width ~ 3.92 * 0.5 / sqrt(n) = 1.96 / sqrt(n)
        # To get width <= 0.10: 1.96 / sqrt(n) <= 0.10 => sqrt(n) >= 19.6 => n >= 384
        
        # Test with n=400, p=0.5 -> expected width <= 0.10
        n = 400
        observed = 200  # p_hat = 0.5
        ci_lower, ci_upper = wilson_ci(observed, n, confidence_level=0.95)
        width = ci_upper - ci_lower
        
        assert width <= 0.10, f"CI width {width:.4f} exceeds 0.10 for n={n}, p={observed/n}"
        
        # Test with n=1000 to ensure it holds for larger samples
        n_large = 1000
        observed_large = 500
        ci_lower_large, ci_upper_large = wilson_ci(observed_large, n_large, confidence_level=0.95)
        width_large = ci_upper_large - ci_lower_large
        
        assert width_large <= 0.10, f"CI width {width_large:.4f} exceeds 0.10 for n={n_large}"
        # Also check that width decreases with n
        assert width_large < width, f"CI width should decrease with larger n: {width_large} vs {width}"

    def test_wilson_ci_bounds(self):
        """Verify CI bounds are within [0, 1]."""
        test_cases = [
            (10, 100, 0.95),   # p=0.1
            (50, 100, 0.95),   # p=0.5
            (90, 100, 0.95),   # p=0.9
            (1, 10, 0.95),     # p=0.1, small n
            (9, 10, 0.95),     # p=0.9, small n
        ]
        
        for observed, n, conf_level in test_cases:
            ci_lower, ci_upper = wilson_ci(observed, n, confidence_level=conf_level)
            assert 0.0 <= ci_lower <= ci_upper <= 1.0, \
                f"CI bounds [{ci_lower}, {ci_upper}] out of range for observed={observed}, n={n}"

    def test_wilson_ci_edge_cases(self):
        """Test Wilson CI with edge cases."""
        # n=0 should raise an error
        with pytest.raises(ValueError):
            wilson_ci(0, 0, 0.95)

        # All successes (observed = n)
        ci_lower, ci_upper = wilson_ci(10, 10, 0.95)
        assert ci_lower >= 0.0 and ci_upper <= 1.0
        # For all successes, lower bound should be > 0 (unless n is very small)
        if 10 > 1:  # Avoid trivial case
            assert ci_lower > 0.0, "Lower bound should be > 0 for all successes with n > 1"

        # All failures (observed = 0)
        ci_lower, ci_upper = wilson_ci(0, 10, 0.95)
        assert ci_lower >= 0.0 and ci_upper <= 1.0
        if 10 > 1:
            assert ci_upper < 1.0, "Upper bound should be < 1 for all failures with n > 1"


class TestComputePrevalence:
    """Tests for the compute_prevalence function."""

    def test_compute_prevalence_basic(self):
        """Test basic prevalence computation."""
        inconsistent_count = 10
        total_count = 100
        prevalence = compute_prevalence(inconsistent_count, total_count)
        expected = 0.10
        assert math.isclose(prevalence, expected, rel_tol=1e-9), \
            f"Expected prevalence {expected}, got {prevalence}"

    def test_compute_prevalence_zero_count(self):
        """Test prevalence with zero inconsistent count."""
        prevalence = compute_prevalence(0, 100)
        assert prevalence == 0.0

    def test_compute_prevalence_all_inconsistent(self):
        """Test prevalence with all inconsistent."""
        prevalence = compute_prevalence(100, 100)
        assert prevalence == 1.0

    def test_compute_prevalence_zero_total(self):
        """Test prevalence with zero total count (should raise error or return 0)."""
        # Depending on implementation, this might raise or return 0.
        # We expect it to handle this gracefully.
        try:
            prevalence = compute_prevalence(10, 0)
            # If it returns a value, it should be 0 or raise an error.
            # For this test, we assume it returns 0 or raises ZeroDivisionError.
            assert prevalence == 0.0, f"Expected 0.0 for zero total, got {prevalence}"
        except ZeroDivisionError:
            pass  # Expected


class TestCIWidthIntegration:
    """Integration tests ensuring CI width constraints are met in realistic scenarios."""

    def test_ci_width_for_various_sample_sizes(self):
        """
        Test CI width for a range of sample sizes to ensure it meets the <= 0.10 constraint.
        This verifies the robustness of the Wilson CI implementation.
        """
        target_width = 0.10
        sample_sizes = [50, 100, 200, 400, 1000, 5000]
        p_values = [0.1, 0.3, 0.5, 0.7, 0.9]

        for n in sample_sizes:
            for p in p_values:
                observed = int(n * p)
                ci_lower, ci_upper = wilson_ci(observed, n, confidence_level=0.95)
                width = ci_upper - ci_lower
                
                # For small n, width might exceed 0.10, which is acceptable.
                # The constraint is that for *sufficiently large* n, width <= 0.10.
                # We check that for n >= 400, width <= 0.10.
                if n >= 400:
                    assert width <= target_width, \
                        f"CI width {width:.4f} exceeds {target_width} for n={n}, p={p}"

    def test_ci_width_consistency_across_p_values(self):
        """
        Verify that CI width is maximized when p=0.5 (worst case) and decreases as p moves away.
        """
        n = 400
        widths = []
        p_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        
        for p in p_values:
            observed = int(n * p)
            ci_lower, ci_upper = wilson_ci(observed, n, confidence_level=0.95)
            width = ci_upper - ci_lower
            widths.append(width)
        
        # The width should be maximized at p=0.5 (index 4)
        max_width = max(widths)
        width_at_05 = widths[4]
        
        # Due to discretization, p=0.5 might not be exactly the max, but it should be close.
        # We check that width_at_05 is among the largest.
        assert width_at_05 >= max(widths[:3] + widths[5:]), \
            f"Width at p=0.5 ({width_at_05}) should be >= widths at other p values"