"""
Unit tests for code/eval/statistical.py

Tests for Wilcoxon signed-rank test, Paired t-test, and Holm-Bonferroni correction.
These tests verify that the statistical functions return valid p-values and
correctly apply multiple hypothesis testing corrections.
"""

import pytest
import numpy as np
from scipy import stats
from eval.statistical import (
    run_paired_ttest,
    run_wilcoxon_test,
    apply_holm_bonferroni,
    run_sensitivity_sweep
)


class TestWilcoxon:
    """Tests for Wilcoxon signed-rank test implementation."""

    def test_wilcoxon_returns_p_value(self):
        """Verify that Wilcoxon test returns a valid p-value (0 <= p <= 1)."""
        # Create two related samples with known properties
        np.random.seed(42)
        sample_a = np.random.normal(loc=10, scale=2, size=50)
        sample_b = sample_a + np.random.normal(loc=0.5, scale=1, size=50)

        statistic, p_value = run_wilcoxon_test(sample_a, sample_b)

        # Verify return types
        assert isinstance(statistic, (float, np.floating)), "Statistic should be a float"
        assert isinstance(p_value, (float, np.floating)), "P-value should be a float"

        # Verify p-value is in valid range
        assert 0.0 <= p_value <= 1.0, f"P-value {p_value} is outside valid range [0, 1]"

        # Verify statistic is non-negative
        assert statistic >= 0, f"Wilcoxon statistic should be non-negative, got {statistic}"

    def test_wilcoxon_identical_samples(self):
        """Verify that identical samples produce p-value of 1.0."""
        sample = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        statistic, p_value = run_wilcoxon_test(sample, sample)

        assert p_value == 1.0, f"Identical samples should have p-value 1.0, got {p_value}"
        assert statistic == 0.0, f"Identical samples should have statistic 0.0, got {statistic}"

    def test_wilcoxon_large_difference(self):
        """Verify that large differences produce small p-values."""
        sample_a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        sample_b = np.array([10.0, 11.0, 12.0, 13.0, 14.0])

        statistic, p_value = run_wilcoxon_test(sample_a, sample_b)

        # With such a large difference, p-value should be very small
        assert p_value < 0.01, f"Large difference should produce small p-value, got {p_value}"


class TestTTest:
    """Tests for Paired t-test implementation."""

    def test_ttest_returns_p_value(self):
        """Verify that paired t-test returns a valid p-value (0 <= p <= 1)."""
        # Create two related samples
        np.random.seed(42)
        sample_a = np.random.normal(loc=10, scale=2, size=50)
        sample_b = sample_a + np.random.normal(loc=0.5, scale=1, size=50)

        statistic, p_value = run_paired_ttest(sample_a, sample_b)

        # Verify return types
        assert isinstance(statistic, (float, np.floating)), "Statistic should be a float"
        assert isinstance(p_value, (float, np.floating)), "P-value should be a float"

        # Verify p-value is in valid range
        assert 0.0 <= p_value <= 1.0, f"P-value {p_value} is outside valid range [0, 1]"

        # Verify statistic can be negative (directional)
        # No assertion on sign, just that it's a number

    def test_ttest_identical_samples(self):
        """Verify that identical samples produce p-value of 1.0."""
        sample = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        statistic, p_value = run_paired_ttest(sample, sample)

        assert p_value == 1.0, f"Identical samples should have p-value 1.0, got {p_value}"
        assert statistic == 0.0, f"Identical samples should have statistic 0.0, got {statistic}"

    def test_ttest_significant_difference(self):
        """Verify that significant differences produce small p-values."""
        sample_a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        sample_b = np.array([10.0, 11.0, 12.0, 13.0, 14.0])

        statistic, p_value = run_paired_ttest(sample_a, sample_b)

        assert p_value < 0.001, f"Significant difference should produce very small p-value, got {p_value}"

    def test_ttest_consistency_with_scipy(self):
        """Verify that our implementation matches scipy.stats.ttest_rel."""
        np.random.seed(123)
        sample_a = np.random.normal(loc=5, scale=1.5, size=100)
        sample_b = sample_a + np.random.normal(loc=0.8, scale=0.5, size=100)

        our_stat, our_p = run_paired_ttest(sample_a, sample_b)
        scipy_stat, scipy_p = stats.ttest_rel(sample_a, sample_b)

        assert np.isclose(our_stat, scipy_stat, rtol=1e-10), \
            f"Statistic mismatch: ours={our_stat}, scipy={scipy_stat}"
        assert np.isclose(our_p, scipy_p, rtol=1e-10), \
            f"P-value mismatch: ours={our_p}, scipy={scipy_p}"


class TestHolmBonferroni:
    """Tests for Holm-Bonferroni multiple hypothesis testing correction."""

    def test_holm_bonferroni_corrects_p_values(self):
        """Verify that Holm-Bonferroni correction adjusts p-values appropriately."""
        # Create a list of raw p-values
        raw_p_values = [0.001, 0.01, 0.02, 0.05, 0.1, 0.2]

        corrected = apply_holm_bonferroni(raw_p_values)

        # Verify return type
        assert isinstance(corrected, list), "Should return a list"
        assert len(corrected) == len(raw_p_values), "Should return same number of p-values"

        # All corrected p-values should be >= their raw counterparts
        for raw, corrected_val in zip(raw_p_values, corrected):
            assert corrected_val >= raw, \
                f"Holm-Bonferroni should increase (or keep) p-values: raw={raw}, corrected={corrected_val}"

        # All p-values should be in valid range
        for p in corrected:
            assert 0.0 <= p <= 1.0, f"Corrected p-value {p} is outside valid range [0, 1]"

    def test_holm_bonferroni_monotonicity(self):
        """Verify that corrected p-values maintain monotonicity with sorted raw p-values."""
        # Sort raw p-values
        raw_p_values = [0.05, 0.01, 0.001, 0.1, 0.02]
        sorted_indices = np.argsort(raw_p_values)
        sorted_raw = [raw_p_values[i] for i in sorted_indices]

        # Apply correction
        corrected = apply_holm_bonferroni(raw_p_values)
        sorted_corrected = [corrected[i] for i in sorted_indices]

        # Corrected p-values should be non-decreasing when sorted by raw p-values
        for i in range(len(sorted_corrected) - 1):
            assert sorted_corrected[i] <= sorted_corrected[i + 1], \
                f"Corrected p-values should be monotonically increasing: {sorted_corrected}"

    def test_holm_bonferroni_single_p_value(self):
        """Verify that a single p-value is handled correctly."""
        raw_p = [0.03]
        corrected = apply_holm_bonferroni(raw_p)

        assert len(corrected) == 1
        assert corrected[0] == 0.03, "Single p-value should remain unchanged"

    def test_holm_bonferroni_all_significant(self):
        """Verify correction when all raw p-values are very small."""
        raw_p_values = [0.0001, 0.0002, 0.0003]
        corrected = apply_holm_bonferroni(raw_p_values)

        # With Holm-Bonferroni, the smallest p-value is multiplied by n,
        # the second by n-1, etc.
        # For [0.0001, 0.0002, 0.0003] sorted:
        # corrected[0] = 0.0001 * 3 = 0.0003
        # corrected[1] = max(0.0002 * 2, corrected[0]) = max(0.0004, 0.0003) = 0.0004
        # corrected[2] = max(0.0003 * 1, corrected[1]) = max(0.0003, 0.0004) = 0.0004

        expected_sorted = [0.0003, 0.0004, 0.0004]
        # Reorder to match original input order
        sorted_indices = np.argsort(raw_p_values)
        inverse_indices = np.argsort(sorted_indices)
        expected = [expected_sorted[i] for i in inverse_indices]

        for c, e in zip(corrected, expected):
            assert np.isclose(c, e, rtol=1e-5), \
                f"Expected {e}, got {c} for input {raw_p_values}"

    def test_holm_bonferroni_capping_at_one(self):
        """Verify that corrected p-values are capped at 1.0."""
        # Create p-values that would exceed 1.0 without capping
        raw_p_values = [0.5, 0.6, 0.7]

        corrected = apply_holm_bonferroni(raw_p_values)

        for p in corrected:
            assert p <= 1.0, f"P-value should be capped at 1.0, got {p}"

    def test_holm_bonferroni_consistency_with_scipy(self):
        """Verify that our implementation matches scipy.stats.multipletests."""
        from statsmodels.stats.multitest import multipletests

        raw_p_values = [0.001, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5]

        our_corrected = apply_holm_bonferroni(raw_p_values)

        # scipy uses 'holm' method in multipletests
        _, scipy_corrected, _, _ = multipletests(raw_p_values, method='holm')

        for our_p, scipy_p in zip(our_corrected, scipy_corrected):
            assert np.isclose(our_p, scipy_p, rtol=1e-10), \
                f"Mismatch at index: ours={our_p}, scipy={scipy_p}"


class TestSensitivitySweep:
    """Tests for sensitivity sweep functionality."""

    def test_sensitivity_sweep_returns_dict(self):
        """Verify that sensitivity sweep returns a dictionary."""
        # Create mock data for a single heuristic
        mock_baseline_scores = np.random.normal(loc=0.8, scale=0.1, size=100)
        mock_heuristic_scores = np.random.normal(loc=0.75, scale=0.12, size=100)

        thresholds = [0.01, 0.05, 0.1]
        result = run_sensitivity_sweep(
            heuristic_name="test_heuristic",
            baseline_scores=mock_baseline_scores,
            heuristic_scores=mock_heuristic_scores,
            thresholds=thresholds,
            test_type="ttest"
        )

        assert isinstance(result, dict), "Should return a dictionary"
        assert "heuristic_name" in result
        assert "thresholds" in result
        assert "results" in result

    def test_sensitivity_sweep_includes_p_values(self):
        """Verify that sensitivity sweep results include p-values."""
        mock_baseline_scores = np.random.normal(loc=0.8, scale=0.1, size=100)
        mock_heuristic_scores = np.random.normal(loc=0.75, scale=0.12, size=100)

        thresholds = [0.01, 0.05, 0.1]
        result = run_sensitivity_sweep(
            heuristic_name="test_heuristic",
            baseline_scores=mock_baseline_scores,
            heuristic_scores=mock_heuristic_scores,
            thresholds=thresholds,
            test_type="ttest"
        )

        results = result["results"]
        assert len(results) == len(thresholds), \
            f"Should have {len(thresholds)} results, got {len(results)}"

        for res in results:
            assert "threshold" in res
            assert "p_value" in res
            assert "statistic" in res
            assert "significant" in res

            # Verify p-value is valid
            assert 0.0 <= res["p_value"] <= 1.0, \
                f"P-value {res['p_value']} is outside valid range"

    def test_sensitivity_sweep_correctness(self):
        """Verify that sensitivity sweep produces expected results for known data."""
        # Create data where we know the relationship
        np.random.seed(42)
        baseline = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        heuristic = baseline + np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])

        thresholds = [0.05]
        result = run_sensitivity_sweep(
            heuristic_name="test",
            baseline_scores=baseline,
            heuristic_scores=heuristic,
            thresholds=thresholds,
            test_type="ttest"
        )

        results = result["results"]
        assert len(results) == 1
        assert results[0]["threshold"] == 0.05
        # With such a small difference, p-value should be relatively large (not significant)
        assert results[0]["p_value"] > 0.05, \
            f"Small difference should produce p-value > 0.05, got {results[0]['p_value']}"
        assert results[0]["significant"] == False, \
            "Should not be significant for small difference"

    def test_sensitivity_sweep_wilcoxon(self):
        """Verify that sensitivity sweep works with Wilcoxon test."""
        mock_baseline_scores = np.random.normal(loc=0.8, scale=0.1, size=100)
        mock_heuristic_scores = np.random.normal(loc=0.75, scale=0.12, size=100)

        thresholds = [0.05]
        result = run_sensitivity_sweep(
            heuristic_name="test_heuristic",
            baseline_scores=mock_baseline_scores,
            heuristic_scores=mock_heuristic_scores,
            thresholds=thresholds,
            test_type="wilcoxon"
        )

        results = result["results"]
        assert len(results) == 1
        assert "p_value" in results[0]
        assert "statistic" in results[0]
        assert 0.0 <= results[0]["p_value"] <= 1.0
