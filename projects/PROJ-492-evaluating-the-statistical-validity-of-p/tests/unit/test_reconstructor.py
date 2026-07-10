"""
Unit tests for the statistical reconstructor module (T024).
Verifies reconstructed p-values and statistics against known fixtures.
"""
import pytest
import numpy as np
from scipy import stats

from code.src.models.data_models import ABTestSummary
from code.src.audit.reconstructor import (
    reconstruct_binary_z_test,
    reconstruct_binary_fisher_test,
    reconstruct_continuous_welch_t_test,
    reconstruct_single_summary,
)


class TestBinaryZTestReconstruction:
    """Tests for two-proportion z-test reconstruction."""

    def test_reconstruct_binary_z_test_known_values(self):
        """Verify z-test reconstruction matches scipy.stats.proportions_ztest."""
        # Known fixture: Control (n=1000, x=100), Treatment (n=1000, x=120)
        n1, x1 = 1000, 100
        n2, x2 = 1000, 120

        # Expected calculation using scipy
        count = np.array([x1, x2])
        nobs = np.array([n1, n2])
        expected_stat, expected_pval = stats.proportions_ztest(count, nobs, alternative='two-sided')

        # Reconstruct using our function
        result_stat, result_pval = reconstruct_binary_z_test(n1, x1, n2, x2)

        # Allow small floating point tolerance
        assert np.isclose(result_stat, expected_stat, rtol=1e-5), f"Stat mismatch: {result_stat} vs {expected_stat}"
        assert np.isclose(result_pval, expected_pval, rtol=1e-5), f"Pval mismatch: {result_pval} vs {expected_pval}"

    def test_reconstruct_binary_z_test_significant_result(self):
        """Test a case with a significant difference."""
        n1, x1 = 500, 50
        n2, x2 = 500, 100
        result_stat, result_pval = reconstruct_binary_z_test(n1, x1, n2, x2)
        assert result_pval < 0.001, "Expected significant p-value for large effect"

    def test_reconstruct_binary_z_test_no_difference(self):
        """Test a case with no difference."""
        n1, x1 = 1000, 100
        n2, x2 = 1000, 100
        result_stat, result_pval = reconstruct_binary_z_test(n1, x1, n2, x2)
        assert np.isclose(result_stat, 0.0, atol=1e-5), "Expected stat ~ 0 for no difference"
        assert np.isclose(result_pval, 1.0, atol=1e-5), "Expected p-value ~ 1.0 for no difference"


class TestBinaryFisherExactReconstruction:
    """Tests for Fisher's exact test reconstruction."""

    def test_reconstruct_binary_fisher_test_known_values(self):
        """Verify Fisher's exact test matches scipy.stats.fisher_exact."""
        # Contingency table: [[x1, n1-x1], [x2, n2-x2]]
        n1, x1 = 20, 10
        n2, x2 = 20, 15

        # Expected calculation using scipy
        table = [[x1, n1 - x1], [x2, n2 - x2]]
        _, expected_pval = stats.fisher_exact(table, alternative='two-sided')

        # Reconstruct using our function
        result_pval = reconstruct_binary_fisher_test(n1, x1, n2, x2)

        assert np.isclose(result_pval, expected_pval, rtol=1e-5), f"Pval mismatch: {result_pval} vs {expected_pval}"

    def test_reconstruct_binary_fisher_test_small_sample(self):
        """Test Fisher's exact with small sample sizes."""
        n1, x1 = 5, 2
        n2, x2 = 5, 4
        result_pval = reconstruct_binary_fisher_test(n1, x1, n2, x2)
        assert 0.0 <= result_pval <= 1.0, "P-value must be between 0 and 1"


class TestContinuousWelchTTestReconstruction:
    """Tests for Welch's t-test reconstruction."""

    def test_reconstruct_continuous_welch_t_test_known_values(self):
        """Verify Welch's t-test reconstruction matches scipy.stats.ttest_ind."""
        # Generate reproducible data
        np.random.seed(42)
        group1 = np.random.normal(loc=10.0, scale=2.0, size=50)
        group2 = np.random.normal(loc=12.0, scale=2.5, size=60)

        # Expected calculation using scipy (equal_var=False for Welch)
        expected_stat, expected_pval = stats.ttest_ind(group1, group2, equal_var=False)

        # Reconstruct using summary statistics (mean, std, n)
        mean1, std1, n1 = np.mean(group1), np.std(group1, ddof=1), len(group1)
        mean2, std2, n2 = np.mean(group2), np.std(group2, ddof=1), len(group2)

        result_stat, result_pval = reconstruct_continuous_welch_t_test(n1, mean1, std1, n2, mean2, std2)

        # Allow for slight numerical differences due to summary vs raw data
        assert np.isclose(result_stat, expected_stat, rtol=1e-4), f"Stat mismatch: {result_stat} vs {expected_stat}"
        assert np.isclose(result_pval, expected_pval, rtol=1e-4), f"Pval mismatch: {result_pval} vs {expected_pval}"

    def test_reconstruct_continuous_welch_t_test_equal_means(self):
        """Test with equal means and variances."""
        np.random.seed(123)
        group1 = np.random.normal(loc=5.0, scale=1.0, size=30)
        group2 = np.random.normal(loc=5.0, scale=1.0, size=30)

        mean1, std1, n1 = np.mean(group1), np.std(group1, ddof=1), len(group1)
        mean2, std2, n2 = np.mean(group2), np.std(group2, ddof=1), len(group2)

        result_stat, result_pval = reconstruct_continuous_welch_t_test(n1, mean1, std1, n2, mean2, std2)
        assert result_pval > 0.05, "Expected non-significant result for equal distributions"


class TestReconstructSingleSummary:
    """Tests for the unified reconstruction entry point."""

    def test_reconstruct_single_summary_binary(self):
        """Test reconstruction of a binary outcome summary."""
        summary = ABTestSummary(
            url="http://example.com/test",
            domain="example.com",
            outcome_type="binary",
            control_n=1000,
            treatment_n=1000,
            control_successes=100,
            treatment_successes=120,
            reported_p_value=0.045,
            reported_effect_size=0.02,
            test_type="z_test"
        )

        result = reconstruct_single_summary(summary)

        assert result is not None
        assert "reconstructed_p_value" in result
        assert "reconstructed_statistic" in result
        assert "test_type_used" in result
        assert result["test_type_used"] == "z_test"
        assert 0.0 <= result["reconstructed_p_value"] <= 1.0

    def test_reconstruct_single_summary_continuous(self):
        """Test reconstruction of a continuous outcome summary."""
        summary = ABTestSummary(
            url="http://example.com/test2",
            domain="example.com",
            outcome_type="continuous",
            control_n=50,
            treatment_n=50,
            control_mean=10.5,
            control_std=2.1,
            treatment_mean=11.2,
            treatment_std=2.3,
            reported_p_value=0.15,
            reported_effect_size=0.7,
            test_type="t_test"
        )

        result = reconstruct_single_summary(summary)

        assert result is not None
        assert "reconstructed_p_value" in result
        assert "test_type_used" in result
        assert result["test_type_used"] == "t_test"

    def test_reconstruct_single_summary_missing_data(self):
        """Test handling of missing required fields."""
        # Binary with missing successes
        summary = ABTestSummary(
            url="http://example.com/bad",
            domain="example.com",
            outcome_type="binary",
            control_n=1000,
            treatment_n=1000,
            control_successes=None,  # Missing
            treatment_successes=120,
            reported_p_value=0.05,
            reported_effect_size=0.02,
            test_type="z_test"
        )

        result = reconstruct_single_summary(summary)
        assert result is not None
        assert result.get("reconstructed_p_value") is None
        assert "error" in result or "warning" in result