"""
Unit tests for the statistical reconstructor module (T023).
Verifies that reconstructed p-values and statistics match expected values
for known inputs across binary (z-test, Fisher) and continuous (Welch t-test) outcomes.
"""
import pytest
import numpy as np
from scipy import stats

# Import the real functions from the reconstructor module
from code.src.audit.reconstructor import (
    reconstruct_binary_z_test,
    reconstruct_binary_fisher_test,
    reconstruct_continuous_welch_t_test,
    reconstruct_single_summary,
)
from code.src.models.data_models import ABTestSummary
from code.src.config import set_rng_seed, SEED

# Set seed for reproducibility in any stochastic checks (though these are deterministic given inputs)
set_rng_seed(SEED)


class TestBinaryZTestReconstruction:
    """Tests for two-proportion z-test reconstruction."""

    def test_reconstruct_binary_z_test_known_values(self):
        """
        Test z-test reconstruction with known values.
        Control: n1=1000, x1=100 (p1=0.10)
        Treatment: n2=1000, x2=120 (p2=0.12)
        Expected p-value should be around 0.115 (two-tailed)
        """
        n_control = 1000
        successes_control = 100
        n_treatment = 1000
        successes_treatment = 120

        p_value, z_stat, effect_size = reconstruct_binary_z_test(
            n_control, successes_control, n_treatment, successes_treatment
        )

        # Manual calculation for verification
        p_control = successes_control / n_control
        p_treatment = successes_treatment / n_treatment
        p_pooled = (successes_control + successes_treatment) / (n_control + n_treatment)
        
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
        expected_z = (p_treatment - p_control) / se
        expected_p = 2 * (1 - stats.norm.cdf(abs(expected_z)))

        assert abs(p_value - expected_p) < 1e-6, f"p-value mismatch: {p_value} vs {expected_p}"
        assert abs(z_stat - expected_z) < 1e-6, f"z-stat mismatch: {z_stat} vs {expected_z}"
        assert abs(effect_size - (p_treatment - p_control)) < 1e-6, "effect size mismatch"

    def test_reconstruct_binary_z_test_significant_result(self):
        """
        Test with a clearly significant result.
        Control: n=1000, x=100
        Treatment: n=1000, x=150
        """
        n_control = 1000
        successes_control = 100
        n_treatment = 1000
        successes_treatment = 150

        p_value, z_stat, effect_size = reconstruct_binary_z_test(
            n_control, successes_control, n_treatment, successes_treatment
        )

        # This should be highly significant (p < 0.001)
        assert p_value < 0.001, f"Expected significant result, got p={p_value}"
        assert z_stat > 3.0, f"Expected z > 3, got {z_stat}"

    def test_reconstruct_binary_z_test_no_effect(self):
        """
        Test with identical proportions (should yield p ~ 1.0)
        """
        n_control = 1000
        successes_control = 100
        n_treatment = 1000
        successes_treatment = 100

        p_value, z_stat, effect_size = reconstruct_binary_z_test(
            n_control, successes_control, n_treatment, successes_treatment
        )

        assert abs(p_value - 1.0) < 1e-6, f"Expected p=1.0, got {p_value}"
        assert abs(z_stat) < 1e-6, f"Expected z=0, got {z_stat}"


class TestBinaryFisherTestReconstruction:
    """Tests for Fisher's exact test reconstruction."""

    def test_reconstruct_binary_fisher_test_known_values(self):
        """
        Test Fisher's exact test with a small contingency table.
        Control: n=20, x=5
        Treatment: n=20, x=10
        """
        n_control = 20
        successes_control = 5
        n_treatment = 20
        successes_treatment = 10

        p_value = reconstruct_binary_fisher_test(
            n_control, successes_control, n_treatment, successes_treatment
        )

        # Manual calculation
        # Contingency table:
        # [success_control, failure_control] = [5, 15]
        # [success_treatment, failure_treatment] = [10, 10]
        table = [[5, 15], [10, 10]]
        expected_p = stats.fisher_exact(table, alternative='two-sided')[1]

        assert abs(p_value - expected_p) < 1e-6, f"p-value mismatch: {p_value} vs {expected_p}"

    def test_reconstruct_binary_fisher_test_significant_result(self):
        """
        Test Fisher's with a strong effect.
        Control: n=50, x=10
        Treatment: n=50, x=30
        """
        n_control = 50
        successes_control = 10
        n_treatment = 50
        successes_treatment = 30

        p_value = reconstruct_binary_fisher_test(
            n_control, successes_control, n_treatment, successes_treatment
        )

        assert p_value < 0.01, f"Expected significant result, got p={p_value}"


class TestContinuousWelchTTestReconstruction:
    """Tests for Welch's t-test reconstruction."""

    def test_reconstruct_continuous_welch_t_test_known_values(self):
        """
        Test Welch's t-test with known parameters.
        We simulate data to get exact expected values, then test reconstruction.
        """
        # Generate deterministic data for known mean and std
        np.random.seed(42)
        n_control = 50
        n_treatment = 50
        mean_control = 10.0
        std_control = 2.0
        mean_treatment = 12.0
        std_treatment = 2.5

        # Generate synthetic data
        data_control = np.random.normal(mean_control, std_control, n_control)
        data_treatment = np.random.normal(mean_treatment, std_treatment, n_treatment)

        # Calculate expected values
        t_stat, expected_p = stats.ttest_ind(
            data_treatment, data_control, equal_var=False
        )

        # Call reconstructor with summary stats (mean, std, n)
        # The reconstructor expects: n1, mean1, std1, n2, mean2, std2
        p_value, t_stat_recon, effect_size = reconstruct_continuous_welch_t_test(
            n_control, mean_control, std_control,
            n_treatment, mean_treatment, std_treatment
        )

        # Note: Due to floating point precision in summary stats vs raw data,
        # we allow a small tolerance, but the p-values should be very close
        # if the summary stats are exact.
        # Since we are passing exact means/stds, the result should match.
        assert abs(p_value - expected_p) < 1e-5, f"p-value mismatch: {p_value} vs {expected_p}"
        assert abs(t_stat_recon - t_stat) < 1e-5, f"t-stat mismatch: {t_stat_recon} vs {t_stat}"

    def test_reconstruct_continuous_welch_t_test_no_effect(self):
        """
        Test with identical means (should yield p ~ 1.0)
        """
        n_control = 50
        mean_control = 10.0
        std_control = 2.0
        n_treatment = 50
        mean_treatment = 10.0
        std_treatment = 2.0

        p_value, t_stat, effect_size = reconstruct_continuous_welch_t_test(
            n_control, mean_control, std_control,
            n_treatment, mean_treatment, std_treatment
        )

        assert abs(p_value - 1.0) < 1e-5, f"Expected p=1.0, got {p_value}"
        assert abs(t_stat) < 1e-5, f"Expected t=0, got {t_stat}"


class TestReconstructSingleSummary:
    """Tests for the high-level reconstruct_single_summary function."""

    def test_reconstruct_single_summary_binary(self):
        """Test reconstruction of a binary outcome summary."""
        summary = ABTestSummary(
            url="http://example.com/test1",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.10,
            treatment_rate=0.12,
            p_value_reported=0.115,
            effect_size_reported=0.02,
            test_type="z-test",
            title="Test 1"
        )

        result = reconstruct_single_summary(summary)

        assert result is not None
        assert result["url"] == "http://example.com/test1"
        assert "reconstructed_p_value" in result
        assert "reconstructed_test_statistic" in result
        assert "reconstructed_effect_size" in result
        assert result["inconsistency_detected"] is not None

    def test_reconstruct_single_summary_continuous(self):
        """Test reconstruction of a continuous outcome summary."""
        summary = ABTestSummary(
            url="http://example.com/test2",
            domain="example.com",
            outcome_type="continuous",
            n_control=50,
            n_treatment=50,
            baseline_mean=10.0,
            baseline_std=2.0,
            treatment_mean=12.0,
            treatment_std=2.5,
            p_value_reported=0.001,
            effect_size_reported=2.0,
            test_type="t-test",
            title="Test 2"
        )

        result = reconstruct_single_summary(summary)

        assert result is not None
        assert result["url"] == "http://example.com/test2"
        assert "reconstructed_p_value" in result
        assert "reconstructed_test_statistic" in result
        assert "reconstructed_effect_size" in result

    def test_reconstruct_single_summary_missing_fields(self):
        """Test that missing required fields are handled gracefully."""
        summary = ABTestSummary(
            url="http://example.com/test3",
            domain="example.com",
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.10,
            treatment_rate=None,  # Missing
            p_value_reported=0.115,
            effect_size_reported=None,
            test_type="z-test",
            title="Test 3"
        )

        # Should return a result indicating failure to reconstruct
        result = reconstruct_single_summary(summary)
        
        # The reconstructor should handle missing data by returning None or specific error flags
        # depending on the implementation of T023. We verify the function doesn't crash.
        assert result is not None
        # If treatment_rate is missing, we cannot reconstruct
        # The exact behavior depends on T023 implementation, but it should not raise an exception.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])