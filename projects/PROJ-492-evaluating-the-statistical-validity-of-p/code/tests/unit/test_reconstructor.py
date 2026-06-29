"""Unit tests for the statistical reconstructor module.

Tests verify that reconstructed p-values, effect sizes, and test statistics
match expected values for known inputs (binary and continuous outcomes).
"""
import pytest
import numpy as np
from datetime import datetime
from code.src.audit.reconstructor import (
    compute_two_proportion_z_test,
    compute_fisher_exact_test,
    compute_welch_t_test,
    reconstruct_from_binary_summary,
    reconstruct_from_continuous_summary,
    reconstruct_p_value,
    validate_reconstruction,
)
from code.src.models.data_models import ABTestSummary

# ============================================================================
# Test Constants - Known expected values for verification
# ============================================================================

# For two-proportion z-test: n1=1000, x1=100, n2=1000, x2=120
# Expected p-value ≈ 0.136 (two-tailed)
BINARY_TEST_1 = {
    "n1": 1000,
    "successes1": 100,
    "n2": 1000,
    "successes2": 120,
    "expected_p_value": 0.136,
    "expected_z_stat": -1.49,
}

# For two-proportion z-test: n1=500, x1=50, n2=500, x2=75
# Expected p-value ≈ 0.034 (two-tailed)
BINARY_TEST_2 = {
    "n1": 500,
    "successes1": 50,
    "n2": 500,
    "successes2": 75,
    "expected_p_value": 0.034,
    "expected_z_stat": -2.12,
}

# For Fisher's exact test: small sample, imbalanced
FISHER_TEST_1 = {
    "n1": 30,
    "successes1": 5,
    "n2": 30,
    "successes2": 15,
    "expected_p_value": 0.032,  # Approximate
}

# For Welch's t-test: known effect
CONTINUOUS_TEST_1 = {
    "n1": 100,
    "mean1": 50.0,
    "std1": 10.0,
    "n2": 100,
    "mean2": 55.0,
    "std2": 10.0,
    "expected_p_value": 0.0003,
    "expected_t_stat": -3.54,
}

# For Welch's t-test: no effect
CONTINUOUS_TEST_2 = {
    "n1": 100,
    "mean1": 50.0,
    "std1": 10.0,
    "n2": 100,
    "mean2": 50.0,
    "std2": 10.0,
    "expected_p_value": 1.0,
    "expected_t_stat": 0.0,
}

# ============================================================================
# Test Classes
# ============================================================================

class TestComputeTwoProportionZTest:
    """Tests for the two-proportion z-test computation."""

    def test_binary_test_1(self):
        """Verify z-test calculation for known binary data."""
        result = compute_two_proportion_z_test(
            n1=BINARY_TEST_1["n1"],
            successes1=BINARY_TEST_1["successes1"],
            n2=BINARY_TEST_1["n2"],
            successes2=BINARY_TEST_1["successes2"],
        )
        assert result["p_value"] is not None
        assert result["z_statistic"] is not None
        # Allow 5% tolerance for expected values
        assert abs(result["p_value"] - BINARY_TEST_1["expected_p_value"]) < 0.01
        assert abs(result["z_statistic"] - BINARY_TEST_1["expected_z_stat"]) < 0.1

    def test_binary_test_2(self):
        """Verify z-test calculation for significant binary data."""
        result = compute_two_proportion_z_test(
            n1=BINARY_TEST_2["n1"],
            successes1=BINARY_TEST_2["successes1"],
            n2=BINARY_TEST_2["n2"],
            successes2=BINARY_TEST_2["successes2"],
        )
        assert result["p_value"] < 0.05  # Should be significant
        assert result["z_statistic"] is not None

    def test_equal_proportions(self):
        """Verify z-test returns p=1.0 when proportions are equal."""
        result = compute_two_proportion_z_test(
            n1=1000, successes1=100, n2=1000, successes2=100
        )
        assert result["p_value"] == 1.0
        assert result["z_statistic"] == 0.0

    def test_small_sample_sizes(self):
        """Verify z-test handles small sample sizes."""
        result = compute_two_proportion_z_test(
            n1=50, successes1=10, n2=50, successes2=20
        )
        assert result["p_value"] is not None
        assert 0 <= result["p_value"] <= 1

    def test_invalid_input_zero_successes(self):
        """Verify z-test handles zero successes gracefully."""
        result = compute_two_proportion_z_test(
            n1=100, successes1=0, n2=100, successes2=10
        )
        assert result["p_value"] is not None
        assert 0 <= result["p_value"] <= 1

    def test_invalid_input_all_successes(self):
        """Verify z-test handles 100% success rates gracefully."""
        result = compute_two_proportion_z_test(
            n1=100, successes1=100, n2=100, successes2=90
        )
        assert result["p_value"] is not None
        assert 0 <= result["p_value"] <= 1


class TestComputeFisherExactTest:
    """Tests for Fisher's exact test computation."""

    def test_fisher_test_1(self):
        """Verify Fisher's test calculation for known small-sample data."""
        result = compute_fisher_exact_test(
            n1=FISHER_TEST_1["n1"],
            successes1=FISHER_TEST_1["successes1"],
            n2=FISHER_TEST_1["n2"],
            successes2=FISHER_TEST_1["successes2"],
        )
        assert result["p_value"] is not None
        assert 0 <= result["p_value"] <= 1

    def test_fisher_equal_proportions(self):
        """Verify Fisher's test returns p=1.0 when proportions are equal."""
        result = compute_fisher_exact_test(
            n1=30, successes1=10, n2=30, successes2=10
        )
        assert result["p_value"] == 1.0

    def test_fisher_extreme_imbalance(self):
        """Verify Fisher's test handles extreme class imbalance."""
        result = compute_fisher_exact_test(
            n1=50, successes1=0, n2=50, successes2=50
        )
        assert result["p_value"] is not None
        assert result["p_value"] < 0.001

    def test_fisher_very_small_sample(self):
        """Verify Fisher's test handles very small samples."""
        result = compute_fisher_exact_test(
            n1=5, successes1=1, n2=5, successes2=4
        )
        assert result["p_value"] is not None
        assert 0 <= result["p_value"] <= 1


class TestComputeWelchTTest:
    """Tests for Welch's t-test computation."""

    def test_continuous_test_1(self):
        """Verify t-test calculation for known continuous data."""
        result = compute_welch_t_test(
            n1=CONTINUOUS_TEST_1["n1"],
            mean1=CONTINUOUS_TEST_1["mean1"],
            std1=CONTINUOUS_TEST_1["std1"],
            n2=CONTINUOUS_TEST_1["n2"],
            mean2=CONTINUOUS_TEST_1["mean2"],
            std2=CONTINUOUS_TEST_1["std2"],
        )
        assert result["p_value"] is not None
        assert result["t_statistic"] is not None
        # Allow 10% tolerance for expected values
        assert abs(result["p_value"] - CONTINUOUS_TEST_1["expected_p_value"]) < 0.0001
        assert abs(result["t_statistic"] - CONTINUOUS_TEST_1["expected_t_stat"]) < 0.1

    def test_continuous_test_2_no_effect(self):
        """Verify t-test returns p=1.0 when means are equal."""
        result = compute_welch_t_test(
            n1=CONTINUOUS_TEST_2["n1"],
            mean1=CONTINUOUS_TEST_2["mean1"],
            std1=CONTINUOUS_TEST_2["std1"],
            n2=CONTINUOUS_TEST_2["n2"],
            mean2=CONTINUOUS_TEST_2["mean2"],
            std2=CONTINUOUS_TEST_2["std2"],
        )
        assert result["p_value"] == 1.0
        assert result["t_statistic"] == 0.0

    def test_welch_unequal_variances(self):
        """Verify Welch's test handles unequal variances correctly."""
        result = compute_welch_t_test(
            n1=100, mean1=50.0, std1=5.0, n2=100, mean2=55.0, std2=15.0
        )
        assert result["p_value"] is not None
        assert 0 <= result["p_value"] <= 1

    def test_very_small_sample_sizes(self):
        """Verify Welch's test handles small samples."""
        result = compute_welch_t_test(
            n1=10, mean1=50.0, std1=10.0, n2=10, mean2=60.0, std2=10.0
        )
        assert result["p_value"] is not None
        assert 0 <= result["p_value"] <= 1


class TestReconstructFromBinarySummary:
    """Tests for binary outcome reconstruction from ABTestSummary."""

    def test_reconstruct_binary_valid(self):
        """Verify reconstruction from valid binary summary."""
        summary = ABTestSummary(
            url="https://example.com/test1",
            domain="example.com",
            publication_year=2023,
            outcome_type="binary",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_p_value=0.136,
        )
        result = reconstruct_from_binary_summary(summary)

        assert result["reconstructed_p_value"] is not None
        assert result["reconstructed_z_statistic"] is not None
        assert result["effect_size"] is not None
        assert result["test_type"] == "z-test"
        assert result["data_quality_warning"] is None

    def test_reconstruct_binary_sample_mismatch(self):
        """Verify warning is generated for sample size mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test2",
            domain="example.com",
            publication_year=2023,
            outcome_type="binary",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            baseline_sample_size=1000,
            treatment_sample_size=500,  # Mismatch
            reported_p_value=0.136,
        )
        result = reconstruct_from_binary_summary(summary)

        assert result["data_quality_warning"] is not None
        assert "sample_size" in result["data_quality_warning"].lower()

    def test_reconstruct_binary_missing_fields(self):
        """Verify graceful handling of missing fields."""
        summary = ABTestSummary(
            url="https://example.com/test3",
            domain="example.com",
            publication_year=2023,
            outcome_type="binary",
            baseline_conversion_rate=None,
            treatment_conversion_rate=0.12,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_p_value=0.136,
        )
        result = reconstruct_from_binary_summary(summary)

        assert result["reconstructed_p_value"] is None
        assert result["data_quality_warning"] is not None


class TestReconstructFromContinuousSummary:
    """Tests for continuous outcome reconstruction from ABTestSummary."""

    def test_reconstruct_continuous_valid(self):
        """Verify reconstruction from valid continuous summary."""
        summary = ABTestSummary(
            url="https://example.com/test4",
            domain="example.com",
            publication_year=2023,
            outcome_type="continuous",
            baseline_mean=50.0,
            treatment_mean=55.0,
            baseline_std=10.0,
            treatment_std=10.0,
            baseline_sample_size=100,
            treatment_sample_size=100,
            reported_p_value=0.0003,
        )
        result = reconstruct_from_continuous_summary(summary)

        assert result["reconstructed_p_value"] is not None
        assert result["reconstructed_t_statistic"] is not None
        assert result["effect_size"] is not None
        assert result["test_type"] == "Welch's t-test"
        assert result["data_quality_warning"] is None

    def test_reconstruct_continuous_sample_mismatch(self):
        """Verify warning is generated for sample size mismatch."""
        summary = ABTestSummary(
            url="https://example.com/test5",
            domain="example.com",
            publication_year=2023,
            outcome_type="continuous",
            baseline_mean=50.0,
            treatment_mean=55.0,
            baseline_std=10.0,
            treatment_std=10.0,
            baseline_sample_size=100,
            treatment_sample_size=50,  # Mismatch
            reported_p_value=0.0003,
        )
        result = reconstruct_from_continuous_summary(summary)

        assert result["data_quality_warning"] is not None
        assert "sample_size" in result["data_quality_warning"].lower()

    def test_reconstruct_continuous_missing_std(self):
        """Verify graceful handling of missing standard deviation."""
        summary = ABTestSummary(
            url="https://example.com/test6",
            domain="example.com",
            publication_year=2023,
            outcome_type="continuous",
            baseline_mean=50.0,
            treatment_mean=55.0,
            baseline_std=None,
            treatment_std=10.0,
            baseline_sample_size=100,
            treatment_sample_size=100,
            reported_p_value=0.0003,
        )
        result = reconstruct_from_continuous_summary(summary)

        assert result["reconstructed_p_value"] is None
        assert result["data_quality_warning"] is not None


class TestReconstructPValue:
    """Tests for the generic p-value reconstruction dispatcher."""

    def test_reconstruct_binary_p_value(self):
        """Verify p-value reconstruction for binary outcomes."""
        summary = ABTestSummary(
            url="https://example.com/test7",
            domain="example.com",
            publication_year=2023,
            outcome_type="binary",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_p_value=0.136,
        )
        result = reconstruct_p_value(summary)

        assert result["reconstructed_p_value"] is not None
        assert result["test_type"] == "z-test"

    def test_reconstruct_continuous_p_value(self):
        """Verify p-value reconstruction for continuous outcomes."""
        summary = ABTestSummary(
            url="https://example.com/test8",
            domain="example.com",
            publication_year=2023,
            outcome_type="continuous",
            baseline_mean=50.0,
            treatment_mean=55.0,
            baseline_std=10.0,
            treatment_std=10.0,
            baseline_sample_size=100,
            treatment_sample_size=100,
            reported_p_value=0.0003,
        )
        result = reconstruct_p_value(summary)

        assert result["reconstructed_p_value"] is not None
        assert result["test_type"] == "Welch's t-test"

    def test_reconstruct_unknown_outcome_type(self):
        """Verify graceful handling of unknown outcome type."""
        summary = ABTestSummary(
            url="https://example.com/test9",
            domain="example.com",
            publication_year=2023,
            outcome_type="unknown",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_p_value=0.136,
        )
        result = reconstruct_p_value(summary)

        assert result["reconstructed_p_value"] is None
        assert result["test_type"] == "fallback"

    def test_reconstruct_missing_required_fields(self):
        """Verify graceful handling of missing required fields."""
        summary = ABTestSummary(
            url="https://example.com/test10",
            domain="example.com",
            publication_year=2023,
            outcome_type="binary",
            baseline_conversion_rate=None,
            treatment_conversion_rate=None,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_p_value=0.136,
        )
        result = reconstruct_p_value(summary)

        assert result["reconstructed_p_value"] is None


class TestValidateReconstruction:
    """Tests for reconstruction validation logic."""

    def test_validate_within_threshold(self):
        """Verify validation passes when p-values are close."""
        reported = 0.136
        reconstructed = 0.140
        result = validate_reconstruction(reported, reconstructed)

        assert result["is_consistent"] is True
        assert result["absolute_difference"] < 0.05

    def test_validate_exceeds_threshold(self):
        """Verify validation fails when p-values differ significantly."""
        reported = 0.01
        reconstructed = 0.10
        result = validate_reconstruction(reported, reconstructed)

        assert result["is_consistent"] is False
        assert result["absolute_difference"] > 0.05

    def test_validate_equal_p_values(self):
        """Verify validation passes when p-values are identical."""
        reported = 0.05
        reconstructed = 0.05
        result = validate_reconstruction(reported, reconstructed)

        assert result["is_consistent"] is True
        assert result["absolute_difference"] == 0.0

    def test_validate_missing_reconstructed(self):
        """Verify validation handles missing reconstructed value."""
        reported = 0.05
        reconstructed = None
        result = validate_reconstruction(reported, reconstructed)

        assert result["is_consistent"] is False
        assert result["validation_error"] is not None

    def test_validate_missing_reported(self):
        """Verify validation handles missing reported value."""
        reported = None
        reconstructed = 0.05
        result = validate_reconstruction(reported, reconstructed)

        assert result["is_consistent"] is False
        assert result["validation_error"] is not None


class TestReconstructorIntegration:
    """Integration tests for the reconstructor module."""

    def test_full_binary_reconstruction_pipeline(self):
        """Test complete binary outcome reconstruction pipeline."""
        summary = ABTestSummary(
            url="https://example.com/integration1",
            domain="example.com",
            publication_year=2023,
            outcome_type="binary",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.12,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_p_value=0.136,
        )

        # Step 1: Reconstruct p-value
        reconstruction = reconstruct_from_binary_summary(summary)

        # Step 2: Validate reconstruction
        validation = validate_reconstruction(
            summary.reported_p_value, reconstruction["reconstructed_p_value"]
        )

        assert reconstruction["reconstructed_p_value"] is not None
        assert validation["absolute_difference"] < 0.05

    def test_full_continuous_reconstruction_pipeline(self):
        """Test complete continuous outcome reconstruction pipeline."""
        summary = ABTestSummary(
            url="https://example.com/integration2",
            domain="example.com",
            publication_year=2023,
            outcome_type="continuous",
            baseline_mean=50.0,
            treatment_mean=55.0,
            baseline_std=10.0,
            treatment_std=10.0,
            baseline_sample_size=100,
            treatment_sample_size=100,
            reported_p_value=0.0003,
        )

        # Step 1: Reconstruct p-value
        reconstruction = reconstruct_from_continuous_summary(summary)

        # Step 2: Validate reconstruction
        validation = validate_reconstruction(
            summary.reported_p_value, reconstruction["reconstructed_p_value"]
        )

        assert reconstruction["reconstructed_p_value"] is not None
        assert validation["absolute_difference"] < 0.001

    def test_inconsistency_detection(self):
        """Test that inconsistency is properly detected."""
        summary = ABTestSummary(
            url="https://example.com/integration3",
            domain="example.com",
            publication_year=2023,
            outcome_type="binary",
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.20,  # Large effect
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            reported_p_value=0.50,  # But claims non-significant (inconsistent)
        )

        reconstruction = reconstruct_from_binary_summary(summary)
        validation = validate_reconstruction(
            summary.reported_p_value, reconstruction["reconstructed_p_value"]
        )

        # The reconstruction should show significant p-value
        assert reconstruction["reconstructed_p_value"] < 0.05
        # But reported was 0.50, so validation should fail
        assert validation["is_consistent"] is False
        assert validation["absolute_difference"] > 0.05