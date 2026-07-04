"""
Unit tests for binomial test and CI width constraint (≤ 0.10).

This module verifies the statistical validity of the prevalence calculations
in src/audit/prevalence.py, specifically ensuring:
1. The binomial test computes correct p-values against known benchmarks.
2. The Wilson confidence interval width does not exceed 0.10 for sufficiently large samples.
3. Sensitivity analysis behaves as expected.
"""
import json
import math
import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from src.audit.prevalence import (
    binomial_test,
    wilson_ci,
    compute_prevalence,
    sensitivity_analysis,
    apply_bonferroni_correction,
    set_rng_seed_for_prevalence,
)
from src.config import SEED


class TestBinomialTest:
    """Tests for the binomial_test function."""

    def test_binomial_test_exact_match(self):
        """Verify binomial test p-value matches scipy.stats.binom_test for a known case."""
        # Case: 15 successes out of 100 trials, null hypothesis p=0.1
        # Expected p-value from scipy.stats.binom_test (two-sided)
        # Using exact calculation or scipy reference
        successes = 15
        n = 100
        p_null = 0.1

        p_val = binomial_test(successes, n, p_null)

        # Reference: scipy.stats.binom_test(successes, n, p_null, alternative='two-sided')
        # Note: scipy.stats.binom_test is deprecated in favor of binomtest, but we check logic
        from scipy import stats
        ref_result = stats.binomtest(successes, n, p_null, alternative="two-sided")
        expected_p = ref_result.pvalue

        assert abs(p_val - expected_p) < 1e-6, f"Binomial test p-value mismatch: {p_val} vs {expected_p}"

    def test_binomial_test_edge_cases(self):
        """Test edge cases: 0 successes, all successes."""
        # 0 successes
        p_val_zero = binomial_test(0, 100, 0.1)
        # When k=0, p-value should be high if p_null is low, but let's just ensure it returns a float in [0,1]
        assert 0.0 <= p_val_zero <= 1.0

        # All successes
        p_val_all = binomial_test(100, 100, 0.1)
        assert 0.0 <= p_val_all <= 1.0

    def test_binomial_test_symmetry(self):
        """Test that swapping successes and failures with (1-p) yields similar logic."""
        # 5 successes out of 100 with p=0.05 vs 95 successes with p=0.95
        # This is a sanity check for the two-sided nature
        p1 = binomial_test(5, 100, 0.05)
        p2 = binomial_test(95, 100, 0.95)
        # They should be very close if the test is symmetric around the null
        assert abs(p1 - p2) < 1e-5


class TestWilsonCI:
    """Tests for the wilson_ci function."""

    def test_wilson_ci_width_constraint(self):
        """Verify that CI width is ≤ 0.10 for sufficiently large N (N >= 300)."""
        # According to FR-025 and SC-024, the audited corpus must meet N >= 300.
        # We test that for N=300, the width is <= 0.10 for a range of proportions.
        n = 300
        proportions = [0.1, 0.3, 0.5, 0.7, 0.9]

        for p in proportions:
            successes = int(n * p)
            lower, upper = wilson_ci(successes, n)
            width = upper - lower
            assert width <= 0.10, f"CI width {width:.4f} exceeds 0.10 for N={n}, p={p}"

    def test_wilson_ci_width_smaller_n(self):
        """Verify that CI width is larger for smaller N (e.g., N=50)."""
        n = 50
        successes = 25
        lower, upper = wilson_ci(successes, n)
        width = upper - lower
        # For small N, width should be significantly larger than 0.10
        assert width > 0.10, f"CI width {width:.4f} should be > 0.10 for small N={n}"

    def test_wilson_ci_symmetry(self):
        """Test that Wilson CI is symmetric around p-hat for p and 1-p."""
        n = 200
        successes = 40
        p_hat = successes / n

        lower1, upper1 = wilson_ci(successes, n)
        center1 = (lower1 + upper1) / 2

        # Inverse case
        successes_inv = n - successes
        lower2, upper2 = wilson_ci(successes_inv, n)
        center2 = (lower2 + upper2) / 2

        # The centers should be symmetric around 0.5
        # center1 should be approx p_hat, center2 should be approx 1 - p_hat
        assert abs(center1 - p_hat) < 1e-6
        assert abs(center2 - (1 - p_hat)) < 1e-6

    def test_wilson_ci_bounds(self):
        """Ensure CI bounds are within [0, 1]."""
        n = 100
        for k in [0, 50, 100]:
            lower, upper = wilson_ci(k, n)
            assert 0.0 <= lower <= 1.0
            assert 0.0 <= upper <= 1.0
            assert lower <= upper


class TestComputePrevalence:
    """Tests for the compute_prevalence function."""

    def test_compute_prevalence_basic(self):
        """Test basic prevalence computation."""
        # Mock audit records
        records = [
            {"is_inconsistent": True},
            {"is_inconsistent": False},
            {"is_inconsistent": True},
            {"is_inconsistent": False},
            {"is_inconsistent": False},
        ]
        result = compute_prevalence(records)

        assert "prevalence" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert "n" in result
        assert result["n"] == 5
        assert abs(result["prevalence"] - 0.4) < 1e-6

    def test_compute_prevalence_empty(self):
        """Test behavior with empty records."""
        result = compute_prevalence([])
        assert result["n"] == 0
        assert result["prevalence"] == 0.0
        # CI should be 0 or handled gracefully
        assert result["ci_lower"] == 0.0
        assert result["ci_upper"] == 0.0


class TestSensitivityAnalysis:
    """Tests for the sensitivity_analysis function."""

    def test_sensitivity_analysis_output(self):
        """Verify sensitivity analysis returns expected structure and variation < 0.02."""
        # Create mock data
        base_prevalence = 0.2
        n = 1000
        records = [{"is_inconsistent": True} if i < base_prevalence * n else {"is_inconsistent": False} for i in range(n)]

        # Run sensitivity analysis with a range of baseline adjustments
        # The function should return a dict with 'sensitivity_results'
        result = sensitivity_analysis(records, baseline_range=[0.9, 1.0, 1.1])

        assert "sensitivity_results" in result
        assert "variation" in result
        
        # The variation should be small (< 0.02) for stable estimates
        assert result["variation"] < 0.02, f"Sensitivity variation {result['variation']} exceeds 0.02"


class TestBonferroniCorrection:
    """Tests for the apply_bonferroni_correction function."""

    def test_bonferroni_correction(self):
        """Verify Bonferroni correction divides alpha by number of tests."""
        alpha = 0.05
        num_tests = 10
        corrected_alpha = apply_bonferroni_correction(alpha, num_tests)
        expected = 0.05 / 10
        assert abs(corrected_alpha - expected) < 1e-9

    def test_bonferroni_single_test(self):
        """Verify no correction for single test."""
        alpha = 0.05
        corrected = apply_bonferroni_correction(alpha, 1)
        assert abs(corrected - alpha) < 1e-9


class TestPrevalenceIntegration:
    """Integration tests for the prevalence module."""

    def test_full_prevalence_pipeline(self):
        """Run a full pipeline: load records, compute prevalence, check CI width."""
        # Simulate a corpus of 300 records with ~10% inconsistency
        n = 300
        inconsistency_rate = 0.10
        records = [
            {"is_inconsistent": True} if i < n * inconsistency_rate else {"is_inconsistent": False}
            for i in range(n)
        ]

        result = compute_prevalence(records)

        # Check prevalence is close to 0.10
        assert abs(result["prevalence"] - 0.10) < 0.05

        # Check CI width <= 0.10 (SC-014 requirement)
        width = result["ci_upper"] - result["ci_lower"]
        assert width <= 0.10, f"CI width {width} exceeds 0.10 for N={n}"

    def test_seed_reproducibility(self):
        """Verify that setting the seed produces reproducible results."""
        set_rng_seed_for_prevalence(SEED)
        n = 100
        records = [{"is_inconsistent": True} if i % 3 == 0 else {"is_inconsistent": False} for i in range(n)]
        
        result1 = compute_prevalence(records)
        
        set_rng_seed_for_prevalence(SEED)
        result2 = compute_prevalence(records)
        
        assert result1["prevalence"] == result2["prevalence"]
        assert result1["ci_lower"] == result2["ci_lower"]
        assert result1["ci_upper"] == result2["ci_upper"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])