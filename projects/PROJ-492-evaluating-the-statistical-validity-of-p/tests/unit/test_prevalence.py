"""
Unit tests for binomial test and CI width <= 0.10 in src.audit.prevalence.

Tests verify:
1. binomial_test returns valid p-values for known inputs.
2. wilson_ci returns intervals with width <= 0.10 for sufficiently large N.
3. Edge cases (N=0, p=0, p=1) are handled correctly.
"""
import pytest
import math
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.prevalence import binomial_test, wilson_ci, set_rng_seed_for_prevalence
from code.src.config import SEED

@pytest.fixture(autouse=True)
def set_seed():
    """Ensure deterministic behavior for all tests."""
    set_rng_seed_for_prevalence(SEED)

class TestBinomialTest:
    """Tests for the binomial_test function."""

    def test_binomial_test_known_values(self):
        """Verify binomial_test returns expected p-values for standard cases."""
        # Case 1: 50 successes out of 100, p=0.5 (should be ~1.0)
        p_val_1 = binomial_test(k=50, n=100, p=0.5)
        assert 0.9 < p_val_1 <= 1.0, f"Expected p-value near 1.0, got {p_val_1}"

        # Case 2: 60 successes out of 100, p=0.5 (should be significant)
        p_val_2 = binomial_test(k=60, n=100, p=0.5)
        assert p_val_2 < 0.05, f"Expected significant p-value, got {p_val_2}"

        # Case 3: Extreme case - 100 successes out of 100, p=0.5
        p_val_3 = binomial_test(k=100, n=100, p=0.5)
        assert p_val_3 == 0.0, "Expected p-value of 0.0 for extreme case"

    def test_binomial_test_edge_cases(self):
        """Test edge cases like n=0 or k=0."""
        # n=0 should handle gracefully (likely return 1.0 or raise specific error)
        # Based on implementation, if n=0, p-value is undefined, usually 1.0 or handled
        try:
            p_val = binomial_test(k=0, n=0, p=0.5)
            # If it returns a value, it should be 1.0 (no evidence against null)
            assert p_val == 1.0, f"Expected 1.0 for n=0, got {p_val}"
        except ValueError:
            # If it raises ValueError, that's also acceptable behavior
            pass

        # k=0, n=10, p=0.5
        p_val = binomial_test(k=0, n=10, p=0.5)
        assert 0 < p_val <= 1.0, f"Invalid p-value for k=0: {p_val}"

    def test_binomial_test_invalid_input(self):
        """Test that invalid inputs raise appropriate errors."""
        with pytest.raises(ValueError):
            binomial_test(k=110, n=100, p=0.5)  # k > n

        with pytest.raises(ValueError):
            binomial_test(k=-1, n=100, p=0.5)  # k < 0

        with pytest.raises(ValueError):
            binomial_test(k=50, n=100, p=1.5)  # p > 1

class TestWilsonCI:
    """Tests for the wilson_ci function."""

    def test_wilson_ci_width_constraint(self):
        """Verify CI width is <= 0.10 for sufficiently large N."""
        # For N=100, p=0.5, width should be small
        ci_lower, ci_upper = wilson_ci(k=50, n=100, alpha=0.05)
        width = ci_upper - ci_lower
        assert width <= 0.10, f"CI width {width} exceeds 0.10 for N=100"

        # For N=400, width should be even smaller
        ci_lower, ci_upper = wilson_ci(k=200, n=400, alpha=0.05)
        width = ci_upper - ci_lower
        assert width <= 0.10, f"CI width {width} exceeds 0.10 for N=400"

    def test_wilson_ci_coverage_properties(self):
        """Verify CI bounds are within [0, 1]."""
        # Test various proportions
        test_cases = [
            (10, 100, 0.05),
            (50, 100, 0.05),
            (90, 100, 0.05),
            (1, 100, 0.05),
            (99, 100, 0.05),
        ]

        for k, n, alpha in test_cases:
            lower, upper = wilson_ci(k, n, alpha)
            assert 0 <= lower <= 1, f"Lower bound {lower} out of range [0, 1]"
            assert 0 <= upper <= 1, f"Upper bound {upper} out of range [0, 1]"
            assert lower <= upper, f"Lower bound {lower} > upper bound {upper}"

    def test_wilson_ci_edge_cases(self):
        """Test Wilson CI for extreme cases."""
        # k=0
        lower, upper = wilson_ci(k=0, n=100, alpha=0.05)
        assert lower == 0.0, f"Expected lower bound 0.0 for k=0, got {lower}"
        assert upper > 0.0, "Expected upper bound > 0.0 for k=0"

        # k=n
        lower, upper = wilson_ci(k=100, n=100, alpha=0.05)
        assert upper == 1.0, f"Expected upper bound 1.0 for k=n, got {upper}"
        assert lower < 1.0, "Expected lower bound < 1.0 for k=n"

        # n=1
        lower, upper = wilson_ci(k=1, n=1, alpha=0.05)
        assert lower < 1.0 and upper == 1.0, "Wilson CI for n=1 should be asymmetric"

    def test_wilson_ci_alpha_sensitivity(self):
        """Verify CI width changes with alpha."""
        k, n = 50, 100
        
        ci_05 = wilson_ci(k, n, alpha=0.05)
        ci_01 = wilson_ci(k, n, alpha=0.01)
        
        width_05 = ci_05[1] - ci_05[0]
        width_01 = ci_01[1] - ci_01[0]
        
        # Higher alpha (0.05) should give narrower CI than lower alpha (0.01)
        assert width_05 < width_01, f"CI width should increase as alpha decreases: {width_05} vs {width_01}"

class TestPrevalenceIntegration:
    """Integration-style tests for prevalence analysis components."""

    def test_binomial_and_wilson_consistency(self):
        """Verify that binomial test and Wilson CI work together logically."""
        # If binomial test is significant (p < 0.05), the CI should not contain 0.5
        k, n, p_null = 60, 100, 0.5
        
        p_val = binomial_test(k, n, p_null)
        ci_lower, ci_upper = wilson_ci(k, n, alpha=0.05)
        
        if p_val < 0.05:
            # If significant, 0.5 should be outside the CI
            assert not (ci_lower <= p_null <= ci_upper), \
                f"Significant p-value {p_val} but CI [{ci_lower}, {ci_upper}] contains {p_null}"
        else:
            # If not significant, 0.5 should be inside the CI
            assert ci_lower <= p_null <= ci_upper, \
                f"Not significant p-value {p_val} but CI [{ci_lower}, {ci_upper}] does not contain {p_null}"

    def test_ci_width_scaling(self):
        """Verify CI width scales correctly with sample size."""
        k_ratio = 0.5
        alphas = [0.05, 0.01]
        
        for alpha in alphas:
            widths = []
            for n in [100, 400, 900]:
                k = int(n * k_ratio)
                lower, upper = wilson_ci(k, n, alpha)
                widths.append(upper - lower)
            
            # Widths should decrease as N increases
            assert widths[0] > widths[1] > widths[2], \
                f"CI widths should decrease with N: {widths}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])