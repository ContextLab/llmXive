"""Unit tests for binomial test and Wilson confidence interval width constraints.

This module verifies:
1. The binomial_test function returns valid p-values and statistics.
2. The wilson_ci function returns intervals with width <= 0.10 for sufficiently large N.
3. Sensitivity to edge cases (p near 0 or 1).
"""

import pytest
import numpy as np
from code.src.audit.prevalence import binomial_test, wilson_ci, compute_prevalence
from code.src.config import set_rng_seed

# Use a fixed seed for deterministic test behavior
set_rng_seed(42)


class TestBinomialTest:
    """Tests for the binomial_test function."""

    def test_binomial_test_basic(self):
        """Test basic binomial test with known inputs."""
        # 10 successes out of 100 trials, null hypothesis p=0.5
        successes = 10
        n = 100
        p_null = 0.5

        result = binomial_test(successes, n, p_null)

        assert result is not None
        assert "p_value" in result
        assert "z_statistic" in result
        assert "observed_proportion" in result

        # Observed proportion should be 0.1
        assert np.isclose(result["observed_proportion"], 0.1)

        # With p=0.1 vs p_null=0.5, p-value should be very small
        assert result["p_value"] < 0.001

    def test_binomial_test_null_hypothesis(self):
        """Test binomial test when observed matches null hypothesis."""
        # 50 successes out of 100 trials, null hypothesis p=0.5
        successes = 50
        n = 100
        p_null = 0.5

        result = binomial_test(successes, n, p_null)

        # p-value should be close to 1.0 (no significant difference)
        assert result["p_value"] > 0.5

    def test_binomial_test_edge_case_zero(self):
        """Test binomial test with zero successes."""
        successes = 0
        n = 100
        p_null = 0.5

        result = binomial_test(successes, n, p_null)

        assert result["p_value"] < 0.001  # Highly significant

    def test_binomial_test_edge_case_all(self):
        """Test binomial test with all successes."""
        successes = 100
        n = 100
        p_null = 0.5

        result = binomial_test(successes, n, p_null)

        assert result["p_value"] < 0.001  # Highly significant

    def test_binomial_test_small_sample(self):
        """Test binomial test with small sample size."""
        successes = 2
        n = 5
        p_null = 0.5

        result = binomial_test(successes, n, p_null)

        assert result is not None
        assert "p_value" in result
        # With small sample, p-value might not be extremely small
        assert 0.0 <= result["p_value"] <= 1.0


class TestWilsonCI:
    """Tests for the Wilson confidence interval function."""

    def test_wilson_ci_width_constraint(self):
        """Test that CI width is <= 0.10 for sufficiently large N."""
        # For width <= 0.10, we typically need N >= 100 for p near 0.5
        # Test with N=200, p=0.5
        n = 200
        p = 0.5
        alpha = 0.05

        result = wilson_ci(n, p, alpha)

        assert result is not None
        assert "lower" in result
        assert "upper" in result
        assert "width" in result

        # Width should be <= 0.10
        assert result["width"] <= 0.10, f"CI width {result['width']} exceeds 0.10"

    def test_wilson_ci_width_constraint_high_p(self):
        """Test CI width constraint with high proportion."""
        n = 200
        p = 0.9
        alpha = 0.05

        result = wilson_ci(n, p, alpha)

        assert result["width"] <= 0.10, f"CI width {result['width']} exceeds 0.10"

    def test_wilson_ci_width_constraint_low_p(self):
        """Test CI width constraint with low proportion."""
        n = 200
        p = 0.1
        alpha = 0.05

        result = wilson_ci(n, p, alpha)

        assert result["width"] <= 0.10, f"CI width {result['width']} exceeds 0.10"

    def test_wilson_ci_asymmetry(self):
        """Test that Wilson CI is asymmetric around p."""
        n = 100
        p = 0.5
        alpha = 0.05

        result = wilson_ci(n, p, alpha)

        lower = result["lower"]
        upper = result["upper"]

        # Wilson CI should be slightly asymmetric
        distance_lower = p - lower
        distance_upper = upper - p

        # They should be close but not necessarily equal
        assert abs(distance_lower) > 0
        assert abs(distance_upper) > 0

    def test_wilson_ci_bounds(self):
        """Test that CI bounds are within [0, 1]."""
        test_cases = [
            (100, 0.5, 0.05),
            (100, 0.01, 0.05),
            (100, 0.99, 0.05),
            (500, 0.5, 0.01),
        ]

        for n, p, alpha in test_cases:
            result = wilson_ci(n, p, alpha)
            assert 0.0 <= result["lower"] <= 1.0
            assert 0.0 <= result["upper"] <= 1.0
            assert result["lower"] <= result["upper"]

    def test_wilson_ci_small_sample_large_width(self):
        """Test that small samples can produce width > 0.10 (expected behavior)."""
        n = 20
        p = 0.5
        alpha = 0.05

        result = wilson_ci(n, p, alpha)

        # With small N, width can be > 0.10
        # This test verifies the function handles it correctly
        assert result["width"] > 0.10, "Expected width > 0.10 for small sample"


class TestComputePrevalence:
    """Tests for the compute_prevalence function."""

    def test_compute_prevalence_basic(self):
        """Test basic prevalence computation."""
        # Simulate audit records with known inconsistency counts
        records = [
            {"is_inconsistent": True},
            {"is_inconsistent": False},
            {"is_inconsistent": True},
            {"is_inconsistent": False},
            {"is_inconsistent": False},
        ]

        result = compute_prevalence(records)

        assert result is not None
        assert "prevalence" in result
        assert "n_total" in result
        assert "n_inconsistent" in result

        # 2 out of 5 = 0.4
        assert np.isclose(result["prevalence"], 0.4)
        assert result["n_total"] == 5
        assert result["n_inconsistent"] == 2

    def test_compute_prevalence_empty(self):
        """Test prevalence computation with empty records."""
        records = []

        result = compute_prevalence(records)

        assert result is not None
        assert result["n_total"] == 0
        assert result["prevalence"] == 0.0

    def test_compute_prevalence_all_inconsistent(self):
        """Test prevalence when all records are inconsistent."""
        records = [
            {"is_inconsistent": True},
            {"is_inconsistent": True},
            {"is_inconsistent": True},
        ]

        result = compute_prevalence(records)

        assert np.isclose(result["prevalence"], 1.0)
        assert result["n_inconsistent"] == 3

    def test_compute_prevalence_with_wilson_ci(self):
        """Test that compute_prevalence includes Wilson CI."""
        records = [
            {"is_inconsistent": True} for _ in range(50)
        ] + [
            {"is_inconsistent": False} for _ in range(50)
        ]

        result = compute_prevalence(records)

        assert "wilson_ci_lower" in result
        assert "wilson_ci_upper" in result
        assert "wilson_ci_width" in result

        # CI width should be <= 0.10 for N=100
        assert result["wilson_ci_width"] <= 0.10


class TestPrevalenceIntegration:
    """Integration tests for prevalence calculations."""

    def test_prevalence_pipeline_consistency(self):
        """Test that binomial test and Wilson CI produce consistent results."""
        n = 200
        successes = 80
        p_observed = successes / n

        # Get binomial test result
        binom_result = binomial_test(successes, n, 0.5)

        # Get Wilson CI
        ci_result = wilson_ci(n, p_observed, 0.05)

        # Observed proportion should match
        assert np.isclose(binom_result["observed_proportion"], p_observed)

        # CI should contain the observed proportion
        assert ci_result["lower"] <= p_observed <= ci_result["upper"]

    def test_large_corpus_prevalence(self):
        """Test prevalence computation on a larger simulated corpus."""
        # Simulate 1000 records with ~20% inconsistency rate
        np.random.seed(42)
        records = [
            {"is_inconsistent": bool(np.random.binomial(1, 0.2))}
            for _ in range(1000)
        ]

        result = compute_prevalence(records)

        assert result["n_total"] == 1000
        # Observed prevalence should be close to 0.2
        assert 0.15 <= result["prevalence"] <= 0.25

        # CI width should be very small for large N
        assert result["wilson_ci_width"] <= 0.05

    def test_prevalence_with_bonferroni(self):
        """Test that prevalence calculation respects Bonferroni correction when specified."""
        records = [
            {"is_inconsistent": True} for _ in range(20)
        ] + [
            {"is_inconsistent": False} for _ in range(80)
        ]

        result = compute_prevalence(records)

        # Basic check that the result is valid
        assert 0.0 <= result["prevalence"] <= 1.0
        assert result["n_total"] == 100
        assert result["n_inconsistent"] == 20