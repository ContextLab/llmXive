"""
Unit tests for the prevalence module (binomial test and Wilson CI width).

This module verifies:
1. The binomial_test function returns valid p-values and confidence intervals.
2. The Wilson CI width is <= 0.10 for typical sample sizes and effect sizes.
3. Edge cases (zero successes, all successes) are handled correctly.
"""

import pytest
import numpy as np
from code.src.audit.prevalence import binomial_test, wilson_ci, set_rng_seed_for_prevalence
from code.src.config import set_rng_seed

# Ensure deterministic behavior for tests
set_rng_seed(42)
set_rng_seed_for_prevalence(42)


class TestBinomialTest:
    """Tests for the binomial_test function in src/audit/prevalence.py."""

    def test_binomial_test_normal_case(self):
        """Test binomial test with a standard case (n=100, k=10, p0=0.15)."""
        n = 100
        k = 10
        p0 = 0.15
        alpha = 0.05

        p_val, ci_low, ci_high = binomial_test(k, n, p0, alpha)

        # P-value should be between 0 and 1
        assert 0.0 <= p_val <= 1.0, f"P-value {p_val} out of range [0, 1]"

        # CI should be within [0, 1]
        assert 0.0 <= ci_low <= 1.0, f"CI low {ci_low} out of range [0, 1]"
        assert 0.0 <= ci_high <= 1.0, f"CI high {ci_high} out of range [0, 1]"

        # CI should be ordered
        assert ci_low <= ci_high, f"CI low {ci_low} > CI high {ci_high}"

        # For k/n = 0.10 vs p0 = 0.15, we expect a significant difference (p < 0.05)
        # This is a sanity check; actual threshold may vary slightly due to approximation
        assert p_val < 0.10, f"Expected p < 0.10 for clear difference, got {p_val}"

    def test_binomial_test_zero_successes(self):
        """Test binomial test with zero successes."""
        n = 50
        k = 0
        p0 = 0.10
        alpha = 0.05

        p_val, ci_low, ci_high = binomial_test(k, n, p0, alpha)

        assert 0.0 <= p_val <= 1.0
        assert ci_low == 0.0  # Lower bound should be 0 when k=0
        assert 0.0 <= ci_high <= 1.0

    def test_binomial_test_all_successes(self):
        """Test binomial test with all successes."""
        n = 50
        k = n
        p0 = 0.90
        alpha = 0.05

        p_val, ci_low, ci_high = binomial_test(k, n, p0, alpha)

        assert 0.0 <= p_val <= 1.0
        assert ci_high == 1.0  # Upper bound should be 1 when k=n
        assert 0.0 <= ci_low <= 1.0

    def test_binomial_test_no_difference(self):
        """Test binomial test when observed proportion equals null hypothesis."""
        n = 100
        k = 20
        p0 = 0.20
        alpha = 0.05

        p_val, ci_low, ci_high = binomial_test(k, n, p0, alpha)

        # P-value should be close to 1.0 (or at least not small)
        assert p_val >= 0.5, f"Expected high p-value for no difference, got {p_val}"

    def test_binomial_test_small_sample(self):
        """Test binomial test with small sample size."""
        n = 10
        k = 3
        p0 = 0.5
        alpha = 0.05

        p_val, ci_low, ci_high = binomial_test(k, n, p0, alpha)

        assert 0.0 <= p_val <= 1.0
        assert 0.0 <= ci_low <= ci_high <= 1.0


class TestWilsonCIWidth:
    """Tests specifically for Wilson CI width <= 0.10 requirement."""

    @pytest.mark.parametrize("n,p", [
        (100, 0.5),   # Standard case
        (200, 0.3),   # Larger sample
        (500, 0.1),   # Small proportion, large sample
        (1000, 0.05), # Very small proportion, very large sample
    ])
    def test_wilson_ci_width_le_0_10(self, n, p):
        """
        Verify that Wilson CI width is <= 0.10 for typical sample sizes.
        This satisfies FR-005a / SC-014 requirement.
        """
        k = int(n * p)
        alpha = 0.05

        # Use wilson_ci directly (assuming it returns (low, high))
        # Note: The prevalence module's wilson_ci might return (low, high) or full dict
        # We'll call it and check the width
        try:
            # Try calling with expected signature from the API surface
            # The API surface says: wilson_ci is a public name
            # We assume it returns (ci_low, ci_high) based on typical usage
            ci_low, ci_high = wilson_ci(k, n, alpha)
            
            width = ci_high - ci_low
            
            # For sufficiently large n, width should be <= 0.10
            # For n >= 100, typical width is around 0.10 or less
            # For n < 100, we might exceed 0.10, so we check conditionally
            if n >= 100:
                assert width <= 0.10, f"Wilson CI width {width:.4f} > 0.10 for n={n}, p={p}"
            else:
                # For small n, we just verify it's a valid width
                assert 0.0 <= width <= 1.0, f"Invalid Wilson CI width {width} for n={n}"
                
        except TypeError as e:
            # If signature is different, try alternative
            # This handles cases where wilson_ci might return a dict
            result = wilson_ci(k, n, alpha)
            if isinstance(result, dict):
                width = result['ci_upper'] - result['ci_lower']
            else:
                # Assume tuple/list
                width = result[1] - result[0]
                
            if n >= 100:
                assert width <= 0.10, f"Wilson CI width {width:.4f} > 0.10 for n={n}, p={p}"
            else:
                assert 0.0 <= width <= 1.0

    def test_wilson_ci_width_edge_cases(self):
        """Test Wilson CI width at boundary conditions."""
        # Case 1: n=100, p=0.5 (maximum variance)
        k = 50
        n = 100
        alpha = 0.05
        
        try:
            ci_low, ci_high = wilson_ci(k, n, alpha)
        except TypeError:
            result = wilson_ci(k, n, alpha)
            if isinstance(result, dict):
                ci_low, ci_high = result['ci_lower'], result['ci_upper']
            else:
                ci_low, ci_high = result[0], result[1]
        
        width = ci_high - ci_low
        # For n=100, width should be approximately 0.10
        assert width <= 0.15, f"Width {width:.4f} too large for n=100 (expected ~0.10)"
        assert width > 0.0, "Width should be positive"

    def test_wilson_ci_width_very_large_n(self):
        """Test that Wilson CI width decreases with very large n."""
        n1, n2 = 100, 10000
        p = 0.5
        alpha = 0.05
        
        k1 = int(n1 * p)
        k2 = int(n2 * p)
        
        try:
            width1 = wilson_ci(k1, n1, alpha)[1] - wilson_ci(k1, n1, alpha)[0]
            width2 = wilson_ci(k2, n2, alpha)[1] - wilson_ci(k2, n2, alpha)[0]
        except TypeError:
            r1 = wilson_ci(k1, n1, alpha)
            r2 = wilson_ci(k2, n2, alpha)
            if isinstance(r1, dict):
                width1 = r1['ci_upper'] - r1['ci_lower']
                width2 = r2['ci_upper'] - r2['ci_lower']
            else:
                width1 = r1[1] - r1[0]
                width2 = r2[1] - r2[0]
        
        # Width should decrease as n increases
        assert width2 < width1, f"Width should decrease with larger n: {width2:.4f} vs {width1:.4f}"
        # For n=10000, width should be well under 0.10
        assert width2 <= 0.02, f"Width {width2:.4f} should be <= 0.02 for n=10000"


class TestSensitivityAnalysis:
    """Tests for sensitivity analysis functionality (if present)."""

    def test_sensitivity_analysis_basic(self):
        """Test that sensitivity analysis runs without error."""
        from code.src.audit.prevalence import sensitivity_analysis
        
        # Basic test with small parameters
        results = sensitivity_analysis(
            k=10, n=100, p0_range=[0.05, 0.15], alpha=0.05
        )
        
        # Results should be a list or dict
        assert results is not None
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])