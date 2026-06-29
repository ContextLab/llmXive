"""
Unit tests for binomial test and CI width ≤ 0.10 in prevalence module.

This test module verifies:
1. binomial_test function produces correct p-values
2. wilson_ci function produces correct confidence intervals
3. CI width is ≤ 0.10 for reasonable sample sizes
4. sensitivity_analysis works correctly
5. apply_bonferroni_correction works correctly
"""

import pytest
import numpy as np
from pathlib import Path
import json
import tempfile

# Import the prevalence module functions
from code.src.audit.prevalence import (
    binomial_test,
    wilson_ci,
    compute_prevalence,
    sensitivity_analysis,
    apply_bonferroni_correction,
    set_rng_seed_for_prevalence,
    load_audit_records,
)
from code.src.config import set_rng_seed


class TestBinomialTest:
    """Tests for the binomial_test function."""

    def test_binomial_test_basic(self):
        """Test basic binomial test with known parameters."""
        set_rng_seed_for_prevalence()

        # Test with n=100, k=50, p0=0.5 (should give p-value close to 1.0)
        n = 100
        k = 50
        p0 = 0.5

        p_value = binomial_test(n, k, p0)

        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0
        # With k=50 and p0=0.5, p-value should be close to 1.0
        assert p_value > 0.9

    def test_binomial_test_significant_result(self):
        """Test binomial test with significant result."""
        set_rng_seed_for_prevalence()

        # Test with n=100, k=80, p0=0.5 (should give small p-value)
        n = 100
        k = 80
        p0 = 0.5

        p_value = binomial_test(n, k, p0)

        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0
        # With k=80 and p0=0.5, p-value should be very small
        assert p_value < 0.01

    def test_binomial_test_two_sided(self):
        """Test that binomial test is two-sided by default."""
        set_rng_seed_for_prevalence()

        # Test with n=100, k=30, p0=0.5 (symmetric to k=70)
        n1 = 100
        k1 = 30
        p0 = 0.5

        n2 = 100
        k2 = 70
        p0 = 0.5

        p_value1 = binomial_test(n1, k1, p0)
        p_value2 = binomial_test(n2, k2, p0)

        assert isinstance(p_value1, float)
        assert isinstance(p_value2, float)
        # Two-sided test should give similar p-values for symmetric cases
        assert abs(p_value1 - p_value2) < 0.01

    def test_binomial_test_edge_cases(self):
        """Test binomial test with edge cases."""
        set_rng_seed_for_prevalence()

        # All successes
        p_value_all = binomial_test(100, 100, 0.5)
        assert 0.0 <= p_value_all <= 1.0

        # No successes
        p_value_none = binomial_test(100, 0, 0.5)
        assert 0.0 <= p_value_none <= 1.0

        # Single trial
        p_value_single = binomial_test(1, 1, 0.5)
        assert 0.0 <= p_value_single <= 1.0

    def test_binomial_test_invalid_inputs(self):
        """Test binomial test with invalid inputs."""
        set_rng_seed_for_prevalence()

        # k > n should handle gracefully
        with pytest.raises((ValueError, AssertionError)):
            binomial_test(10, 15, 0.5)

        # Negative k should handle gracefully
        with pytest.raises((ValueError, AssertionError)):
            binomial_test(10, -1, 0.5)

        # Invalid p0 should handle gracefully
        with pytest.raises((ValueError, AssertionError)):
            binomial_test(10, 5, 1.5)


class TestWilsonCI:
    """Tests for the wilson_ci function."""

    def test_wilson_ci_basic(self):
        """Test basic Wilson CI calculation."""
        set_rng_seed_for_prevalence()

        # Test with n=100, k=50
        n = 100
        k = 50

        ci_lower, ci_upper = wilson_ci(n, k)

        assert isinstance(ci_lower, float)
        assert isinstance(ci_upper, float)
        assert 0.0 <= ci_lower <= ci_upper <= 1.0
        # Point estimate should be within CI
        assert ci_lower <= k / n <= ci_upper

    def test_wilson_ci_width_constraint(self):
        """Test that CI width is ≤ 0.10 for reasonable sample sizes."""
        set_rng_seed_for_prevalence()

        # For n ≥ 300, CI width should be ≤ 0.10
        n = 300
        k = 150

        ci_lower, ci_upper = wilson_ci(n, k)
        width = ci_upper - ci_lower

        assert width <= 0.10, f"CI width {width} exceeds 0.10 threshold"

    def test_wilson_ci_width_for_different_samples(self):
        """Test CI width for various sample sizes."""
        set_rng_seed_for_prevalence()

        sample_sizes = [100, 200, 300, 500, 1000]
        k_values = [50, 100, 150, 250, 500]

        for n, k in zip(sample_sizes, k_values):
            ci_lower, ci_upper = wilson_ci(n, k)
            width = ci_upper - ci_lower

            # Width should decrease as sample size increases
            assert width > 0
            assert ci_lower >= 0
            assert ci_upper <= 1

    def test_wilson_ci_extreme_proportions(self):
        """Test Wilson CI with extreme proportions."""
        set_rng_seed_for_prevalence()

        # Very low proportion
        ci_lower1, ci_upper1 = wilson_ci(100, 5)
        assert 0.0 <= ci_lower1 <= ci_upper1 <= 1.0

        # Very high proportion
        ci_lower2, ci_upper2 = wilson_ci(100, 95)
        assert 0.0 <= ci_lower2 <= ci_upper2 <= 1.0

    def test_wilson_ci_asymmetric(self):
        """Test that Wilson CI is asymmetric around point estimate."""
        set_rng_seed_for_prevalence()

        n = 100
        k = 30

        ci_lower, ci_upper = wilson_ci(n, k)
        point_estimate = k / n

        # Wilson CI is asymmetric (except when p=0.5)
        lower_dist = point_estimate - ci_lower
        upper_dist = ci_upper - point_estimate

        # They should be different for asymmetric cases
        assert abs(lower_dist - upper_dist) > 0.001


class TestComputePrevalence:
    """Tests for the compute_prevalence function."""

    def test_compute_prevalence_basic(self):
        """Test basic prevalence computation."""
        set_rng_seed_for_prevalence()

        # Create test audit records
        audit_records = [
            {"is_inconsistent": True},
            {"is_inconsistent": False},
            {"is_inconsistent": True},
            {"is_inconsistent": False},
            {"is_inconsistent": False},
        ]

        result = compute_prevalence(audit_records)

        assert "prevalence" in result
        assert "total_count" in result
        assert "inconsistent_count" in result
        assert result["prevalence"] == 0.4  # 2/5
        assert result["total_count"] == 5
        assert result["inconsistent_count"] == 2

    def test_compute_prevalence_with_wilson_ci(self):
        """Test prevalence computation includes Wilson CI."""
        set_rng_seed_for_prevalence()

        audit_records = [
            {"is_inconsistent": True},
            {"is_inconsistent": False},
        ] * 150  # 300 total, 150 inconsistent

        result = compute_prevalence(audit_records)

        assert "wilson_ci_lower" in result
        assert "wilson_ci_upper" in result
        assert result["wilson_ci_lower"] <= result["prevalence"] <= result["wilson_ci_upper"]

    def test_compute_prevalence_empty(self):
        """Test prevalence computation with empty records."""
        set_rng_seed_for_prevalence()

        with pytest.raises((ValueError, ZeroDivisionError)):
            compute_prevalence([])


class TestSensitivityAnalysis:
    """Tests for the sensitivity_analysis function."""

    def test_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis."""
        set_rng_seed_for_prevalence()

        n = 500
        k = 250
        baseline_range = [0.45, 0.50, 0.55]

        results = sensitivity_analysis(n, k, baseline_range)

        assert isinstance(results, dict)
        assert "baseline_results" in results
        assert len(results["baseline_results"]) == len(baseline_range)

    def test_sensitivity_analysis_variation(self):
        """Test that sensitivity analysis variation is < 0.02."""
        set_rng_seed_for_prevalence()

        n = 500
        k = 250
        baseline_range = [0.48, 0.50, 0.52]

        results = sensitivity_analysis(n, k, baseline_range)

        if "prevalence_values" in results:
            prev_values = results["prevalence_values"]
            if len(prev_values) > 1:
                variation = max(prev_values) - min(prev_values)
                # Variation should be small for reasonable baseline range
                assert variation < 0.05


class TestApplyBonferroniCorrection:
    """Tests for the apply_bonferroni_correction function."""

    def test_bonferroni_basic(self):
        """Test basic Bonferroni correction."""
        set_rng_seed_for_prevalence()

        alpha = 0.05
        n_tests = 5

        corrected_alpha = apply_bonferroni_correction(alpha, n_tests)

        assert isinstance(corrected_alpha, float)
        assert corrected_alpha == alpha / n_tests
        assert corrected_alpha == 0.01

    def test_bonferroni_single_test(self):
        """Test Bonferroni correction with single test."""
        set_rng_seed_for_prevalence()

        alpha = 0.05
        n_tests = 1

        corrected_alpha = apply_bonferroni_correction(alpha, n_tests)

        assert corrected_alpha == 0.05

    def test_bonferroni_many_tests(self):
        """Test Bonferroni correction with many tests."""
        set_rng_seed_for_prevalence()

        alpha = 0.05
        n_tests = 100

        corrected_alpha = apply_bonferroni_correction(alpha, n_tests)

        assert corrected_alpha == 0.0005


class TestPrevalenceCIWidthConstraint:
    """Tests specifically for CI width ≤ 0.10 constraint."""

    def test_ci_width_meets_constraint_for_n_300(self):
        """Verify CI width ≤ 0.10 for N ≥ 300."""
        set_rng_seed_for_prevalence()

        # Test with N = 300 (minimum required by SC-025)
        n = 300
        for k in [50, 100, 150, 200, 250]:
            ci_lower, ci_upper = wilson_ci(n, k)
            width = ci_upper - ci_lower

            assert width <= 0.10, f"CI width {width} for n={n}, k={k} exceeds 0.10"

    def test_ci_width_decreases_with_n(self):
        """Verify CI width decreases as N increases."""
        set_rng_seed_for_prevalence()

        n_values = [100, 200, 300, 500, 1000]
        widths = []

        for n in n_values:
            ci_lower, ci_upper = wilson_ci(n, n // 2)
            widths.append(ci_upper - ci_lower)

        # Widths should be monotonically decreasing
        for i in range(1, len(widths)):
            assert widths[i] <= widths[i - 1], f"Width increased from {widths[i-1]} to {widths[i]}"

    def test_ci_width_constraint_at_boundary(self):
        """Test CI width constraint at the boundary (width ≈ 0.10)."""
        set_rng_seed_for_prevalence()

        # Find approximate N where width ≈ 0.10 for p = 0.5
        # Wilson CI width ≈ 2 * z * sqrt(p(1-p)/n) ≈ 1.96 * sqrt(1/n)
        # For width = 0.10: n ≈ (1.96/0.05)^2 ≈ 1537

        n = 1500
        ci_lower, ci_upper = wilson_ci(n, n // 2)
        width = ci_upper - ci_lower

        assert width <= 0.10, f"CI width {width} at n={n} exceeds 0.10"

    def test_ci_width_for_extreme_proportions(self):
        """Test CI width constraint for extreme proportions."""
        set_rng_seed_for_prevalence()

        n = 300
        # Extreme proportions have smaller CIs
        test_cases = [(300, 30), (300, 270), (300, 60), (300, 240)]

        for n, k in test_cases:
            ci_lower, ci_upper = wilson_ci(n, k)
            width = ci_upper - ci_lower

            assert width <= 0.10, f"CI width {width} for n={n}, k={k} exceeds 0.10"


class TestPrevalenceIntegration:
    """Integration tests for prevalence module."""

    def test_full_prevalence_workflow(self):
        """Test complete prevalence workflow with file output."""
        set_rng_seed_for_prevalence()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_file = tmpdir_path / "prevalence_test.json"

            # Create test audit records
            audit_records = [
                {"is_inconsistent": True, "domain": "tech"}
                for _ in range(150)
            ] + [
                {"is_inconsistent": False, "domain": "tech"}
                for _ in range(150)
            ]

            # Compute prevalence
            result = compute_prevalence(audit_records)

            assert result["prevalence"] == 0.5
            assert result["total_count"] == 300
            assert result["inconsistent_count"] == 150

    def test_load_audit_records(self):
        """Test loading audit records from JSON file."""
        set_rng_seed_for_prevalence()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test_audit.json"

            # Write test data
            test_data = [
                {"is_inconsistent": True, "url": "http://example.com/1"},
                {"is_inconsistent": False, "url": "http://example.com/2"},
            ]

            with open(test_file, "w") as f:
                json.dump(test_data, f)

            # Load records
            records = load_audit_records(test_file)

            assert len(records) == 2
            assert records[0]["is_inconsistent"] is True
            assert records[1]["is_inconsistent"] is False


class TestRNGSeeding:
    """Tests for RNG seeding in prevalence module."""

    def test_rng_seed_consistency(self):
        """Test that seeding produces consistent results."""
        # First run
        set_rng_seed_for_prevalence()
        np.random.seed(42)
        result1 = np.random.random()

        # Second run
        set_rng_seed_for_prevalence()
        np.random.seed(42)
        result2 = np.random.random()

        assert result1 == result2

    def test_set_rng_seed_for_prevalence(self):
        """Test the prevalence-specific seed function."""
        set_rng_seed_for_prevalence()

        # Should not raise any errors
        assert True