"""
Unit tests for binomial test and CI width <= 0.10 (Task T043).

These tests verify:
1. The binomial test function returns valid p-values.
2. The Wilson Confidence Interval width is <= 0.10 for sufficiently large N.
3. Edge cases (N=0, p=0, p=1) are handled correctly.
"""
import pytest
import json
import math
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Import from the project's source
# Ensure the code directory is in the path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.prevalence import (
    binomial_test,
    wilson_ci,
    compute_prevalence,
    set_rng_seed_for_prevalence
)
from code.src.config import set_rng_seed


class TestBinomialTest:
    """Tests for the binomial_test function."""

    def test_binomial_test_standard_case(self):
        """Test binomial test with a standard scenario."""
        # n=100, k=50 (p=0.5), null hypothesis p0=0.5
        # Expected p-value should be 1.0 (perfect match)
        p_val = binomial_test(n=100, k=50, p0=0.5)
        assert p_val == 1.0, f"Expected 1.0, got {p_val}"

    def test_binomial_test_significant_difference(self):
        """Test binomial test with a significant difference."""
        # n=100, k=90 (p=0.9), null hypothesis p0=0.5
        # This should be highly significant (p < 0.05)
        p_val = binomial_test(n=100, k=90, p0=0.5)
        assert p_val < 0.05, f"Expected p < 0.05, got {p_val}"

    def test_binomial_test_edge_case_zero_successes(self):
        """Test binomial test with zero successes."""
        p_val = binomial_test(n=100, k=0, p0=0.5)
        # Should be extremely small but not necessarily 0 due to float precision
        assert 0 <= p_val <= 1e-20, f"Expected very small p-value, got {p_val}"

    def test_binomial_test_edge_case_all_successes(self):
        """Test binomial test with all successes."""
        p_val = binomial_test(n=100, k=100, p0=0.5)
        assert 0 <= p_val <= 1e-20, f"Expected very small p-value, got {p_val}"

    def test_binomial_test_invalid_n(self):
        """Test binomial test with invalid n (negative)."""
        with pytest.raises(ValueError):
            binomial_test(n=-1, k=0, p0=0.5)

    def test_binomial_test_k_greater_than_n(self):
        """Test binomial test with k > n."""
        with pytest.raises(ValueError):
            binomial_test(n=10, k=11, p0=0.5)


class TestWilsonCI:
    """Tests for the Wilson Confidence Interval function."""

    def test_wilson_ci_width_small_n(self):
        """Test Wilson CI width with small N (should be wide)."""
        # n=10, k=5
        lower, upper = wilson_ci(n=10, k=5, confidence=0.95)
        width = upper - lower
        # For small N, width should be large (> 0.10)
        assert width > 0.10, f"Expected width > 0.10 for small N, got {width}"

    def test_wilson_ci_width_large_n(self):
        """Test Wilson CI width with large N (should be <= 0.10)."""
        # n=1000, k=500 -> p=0.5
        # Expected width should be small
        lower, upper = wilson_ci(n=1000, k=500, confidence=0.95)
        width = upper - lower
        assert width <= 0.10, f"Expected width <= 0.10 for large N, got {width}"

    def test_wilson_ci_width_very_large_n(self):
        """Test Wilson CI width with very large N (should be very narrow)."""
        # n=10000, k=5000
        lower, upper = wilson_ci(n=10000, k=5000, confidence=0.95)
        width = upper - lower
        assert width <= 0.05, f"Expected width <= 0.05 for very large N, got {width}"

    def test_wilson_ci_bounds_valid(self):
        """Test that Wilson CI bounds are within [0, 1]."""
        lower, upper = wilson_ci(n=100, k=50, confidence=0.95)
        assert 0 <= lower <= upper <= 1, f"CI bounds out of range: [{lower}, {upper}]"

    def test_wilson_ci_edge_case_zero_successes(self):
        """Test Wilson CI with zero successes."""
        lower, upper = wilson_ci(n=100, k=0, confidence=0.95)
        assert 0 <= lower <= upper <= 1, f"CI bounds out of range: [{lower}, {upper}]"
        # Lower bound should be 0 or very close to 0
        assert lower == 0 or math.isclose(lower, 0, abs_tol=1e-6)

    def test_wilson_ci_edge_case_all_successes(self):
        """Test Wilson CI with all successes."""
        lower, upper = wilson_ci(n=100, k=100, confidence=0.95)
        assert 0 <= lower <= upper <= 1, f"CI bounds out of range: [{lower}, {upper}]"
        # Upper bound should be 1 or very close to 1
        assert upper == 1 or math.isclose(upper, 1, abs_tol=1e-6)

    def test_wilson_ci_symmetry(self):
        """Test symmetry of Wilson CI for p and 1-p."""
        n = 100
        lower1, upper1 = wilson_ci(n=n, k=30, confidence=0.95)
        lower2, upper2 = wilson_ci(n=n, k=70, confidence=0.95)
        
        # The interval for 30/100 should be symmetric to 70/100 around 0.5
        # i.e., lower1 = 1 - upper2, upper1 = 1 - lower2
        assert math.isclose(lower1, 1 - upper2, abs_tol=1e-6), "Symmetry check failed for lower bound"
        assert math.isclose(upper1, 1 - lower2, abs_tol=1e-6), "Symmetry check failed for upper bound"


class TestComputePrevalence:
    """Tests for the compute_prevalence function."""

    def test_compute_prevalence_basic(self):
        """Test compute_prevalence with a simple dataset."""
        # Create mock audit records
        records = [
            {"is_inconsistent": True},
            {"is_inconsistent": False},
            {"is_inconsistent": True},
            {"is_inconsistent": False},
            {"is_inconsistent": False}
        ]
        
        result = compute_prevalence(records)
        
        assert "prevalence" in result
        assert "n_total" in result
        assert "n_inconsistent" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        
        assert result["n_total"] == 5
        assert result["n_inconsistent"] == 2
        assert math.isclose(result["prevalence"], 0.4, abs_tol=1e-6)

    def test_compute_prevalence_empty_list(self):
        """Test compute_prevalence with an empty list."""
        with pytest.raises(ValueError):
            compute_prevalence([])

    def test_compute_prevalence_all_inconsistent(self):
        """Test compute_prevalence when all records are inconsistent."""
        records = [
            {"is_inconsistent": True},
            {"is_inconsistent": True},
            {"is_inconsistent": True}
        ]
        
        result = compute_prevalence(records)
        assert math.isclose(result["prevalence"], 1.0, abs_tol=1e-6)
        assert result["n_inconsistent"] == 3

    def test_compute_prevalence_ci_width_constraint(self):
        """
        Test that for a sufficiently large corpus, the CI width is <= 0.10.
        This directly addresses the task requirement: "CI width <= 0.10".
        """
        # Simulate a large corpus (N >= 300 as per FR-025/SC-025)
        # We need enough samples such that the Wilson CI width <= 0.10
        # For p=0.5, n=97 gives width ~0.10. For n=300, width is much smaller.
        
        # Create 300 mock records with 50% inconsistency
        records = [{"is_inconsistent": i % 2 == 0} for i in range(300)]
        
        result = compute_prevalence(records)
        ci_width = result["ci_upper"] - result["ci_lower"]
        
        assert ci_width <= 0.10, f"CI width {ci_width} exceeds 0.10 threshold for N=300"

    def test_compute_prevalence_seed_reproducibility(self):
        """Test that seeding produces reproducible results (if randomness is involved)."""
        # Although compute_prevalence is deterministic, we test the seed setup
        set_rng_seed_for_prevalence(42)
        records = [{"is_inconsistent": i % 2 == 0} for i in range(100)]
        result1 = compute_prevalence(records)
        
        set_rng_seed_for_prevalence(42)
        result2 = compute_prevalence(records)
        
        # Results should be identical
        assert result1 == result2, "Results differ despite same seed"


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_prevalence_pipeline(self):
        """Test the full prevalence pipeline with a realistic scenario."""
        # Generate a realistic set of audit records
        # Simulate a corpus of 500 summaries with ~15% inconsistency rate
        n_total = 500
        inconsistency_rate = 0.15
        n_inconsistent = int(n_total * inconsistency_rate)
        
        records = []
        for i in range(n_total):
            is_inconsistent = i < n_inconsistent
            records.append({"is_inconsistent": is_inconsistent})
        
        result = compute_prevalence(records)
        
        # Verify basic counts
        assert result["n_total"] == n_total
        assert result["n_inconsistent"] == n_inconsistent
        assert math.isclose(result["prevalence"], inconsistency_rate, abs_tol=1e-6)
        
        # Verify CI width constraint
        ci_width = result["ci_upper"] - result["ci_lower"]
        assert ci_width <= 0.10, f"CI width {ci_width} exceeds 0.10 for N={n_total}"
        
        # Verify bounds
        assert 0 <= result["ci_lower"] <= result["prevalence"] <= result["ci_upper"] <= 1

    def test_precision_recall_implications(self):
        """
        Test implications for precision/recall calculations.
        If we treat 'inconsistent' as 'positive', we can verify
        that the prevalence estimate is stable.
        """
        # Create a dataset where we know the true prevalence
        true_prevalence = 0.20
        n = 1000
        
        # Deterministic generation based on true prevalence
        records = [{"is_inconsistent": i < int(n * true_prevalence)} for i in range(n)]
        
        result = compute_prevalence(records)
        
        # The estimated prevalence should match the true prevalence
        assert math.isclose(result["prevalence"], true_prevalence, abs_tol=0.01)
        
        # CI should be narrow enough
        ci_width = result["ci_upper"] - result["ci_lower"]
        assert ci_width <= 0.10, f"CI width {ci_width} too wide for N={n}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])