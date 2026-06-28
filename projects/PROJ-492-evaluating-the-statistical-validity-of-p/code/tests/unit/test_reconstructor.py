"""
Unit tests for statistical reconstruction module.

Tests cover binary (z-test, Fisher's exact) and continuous (Welch's t-test)
reconstruction with known fixtures and expected outputs.
"""
import pytest
import numpy as np
from datetime import datetime

from code.src.audit.reconstructor import (
    reconstruct_p_value,
    reconstruct_from_binary_summary,
    reconstruct_from_continuous_summary,
    validate_reconstruction,
    ReconstructionResult,
    _compute_two_proportion_z_test,
    _compute_fisher_exact_test,
    _compute_welch_t_test,
)
from code.src.models.data_models import ABTestSummary


class TestComputeTwoProportionZTest:
    """Tests for two-proportion z-test computation."""

    def test_basic_binary_case(self):
        """Test basic binary outcome with known values."""
        # Control: 100 samples, 20 successes (20%)
        # Treatment: 100 samples, 30 successes (30%)
        p_value, effect_size = _compute_two_proportion_z_test(
            n_control=100,
            n_treatment=100,
            success_control=20,
            success_treatment=30,
        )
        assert not np.isnan(p_value)
        assert not np.isnan(effect_size)
        assert effect_size == pytest.approx(0.10, rel=0.01)
        # P-value should be reasonable (not 0 or 1 for this effect size)
        assert 0 < p_value < 1

    def test_equal_proportions(self):
        """Test when proportions are equal (p-value should be ~1)."""
        p_value, effect_size = _compute_two_proportion_z_test(
            n_control=100,
            n_treatment=100,
            success_control=25,
            success_treatment=25,
        )
        assert not np.isnan(p_value)
        assert effect_size == pytest.approx(0.0, abs=0.01)
        assert p_value > 0.9  # Should be close to 1

    def test_invalid_sample_sizes(self):
        """Test with invalid sample sizes returns NaN."""
        p_value, effect_size = _compute_two_proportion_z_test(
            n_control=0,
            n_treatment=100,
            success_control=0,
            success_treatment=10,
        )
        assert np.isnan(p_value)
        assert np.isnan(effect_size)


class TestComputeFisherExactTest:
    """Tests for Fisher's exact test computation."""

    def test_small_sample_binary(self):
        """Test Fisher's exact test with small samples."""
        # Small samples where Fisher's is preferred
        p_value, effect_size = _compute_fisher_exact_test(
            success_control=5,
            success_treatment=12,
            n_control=20,
            n_treatment=20,
        )
        assert not np.isnan(p_value)
        assert not np.isnan(effect_size)
        assert 0 <= p_value <= 1

    def test_all_successes_control(self):
        """Test edge case where all control succeed."""
        p_value, effect_size = _compute_fisher_exact_test(
            success_control=20,
            success_treatment=10,
            n_control=20,
            n_treatment=20,
        )
        assert not np.isnan(p_value)
        assert 0 <= p_value <= 1

    def test_invalid_sample_sizes(self):
        """Test with invalid sample sizes."""
        p_value, effect_size = _compute_fisher_exact_test(
            success_control=5,
            success_treatment=10,
            n_control=0,
            n_treatment=20,
        )
        assert np.isnan(p_value)
        assert np.isnan(effect_size)


class TestComputeWelchTTest:
    """Tests for Welch's t-test computation."""

    def test_basic_continuous_case(self):
        """Test basic continuous outcome."""
        p_value, effect_size = _compute_welch_t_test(
            mean_control=50.0,
            mean_treatment=55.0,
            std_control=10.0,
            std_treatment=10.0,
            n_control=100,
            n_treatment=100,
        )
        assert not np.isnan(p_value)
        assert not np.isnan(effect_size)
        assert 0 <= p_value <= 1

    def test_equal_means(self):
        """Test when means are equal (p-value should be ~1)."""
        p_value, effect_size = _compute_welch_t_test(
            mean_control=50.0,
            mean_treatment=50.0,
            std_control=10.0,
            std_treatment=10.0,
            n_control=100,
            n_treatment=100,
        )
        assert not np.isnan(p_value)
        assert effect_size == pytest.approx(0.0, abs=0.01)
        assert p_value > 0.9

    def test_invalid_sample_sizes(self):
        """Test with invalid sample sizes."""
        p_value, effect_size = _compute_welch_t_test(
            mean_control=50.0,
            mean_treatment=55.0,
            std_control=10.0,
            std_treatment=10.0,
            n_control=0,
            n_treatment=100,
        )
        assert np.isnan(p_value)
        assert np.isnan(effect_size)


class TestReconstructFromBinarySummary:
    """Tests for binary summary reconstruction."""

    def test_binary_summary_reconstruction(self):
        """Test reconstruction from ABTestSummary with binary outcome."""
        summary = ABTestSummary(
            source_url='https://example.com/test1',
            domain='tech',
            publication_year=2023,
            sample_size_control=1000,
            sample_size_treatment=1000,
            successes_control=200,
            successes_treatment=250,
            baseline_conversion_rate=0.20,
            reported_p_value=0.008,
            reported_effect_size=0.05,
            test_timestamp=datetime(2023, 6, 15),
        )

        result = reconstruct_from_binary_summary(summary)

        assert result.success
        assert result.test_type in ['binary_z_test', 'binary_fisher']
        assert not np.isnan(result.reconstructed_p_value)
        assert not np.isnan(result.reconstructed_effect_size)
        assert result.absolute_p_difference < 1.0  # Should be reasonable

    def test_binary_summary_with_fallback(self):
        """Test reconstruction when baseline is missing (FR-012 fallback)."""
        summary = ABTestSummary(
            source_url='https://example.com/test2',
            domain='tech',
            publication_year=2023,
            sample_size_control=500,
            sample_size_treatment=500,
            successes_control=100,
            successes_treatment=125,
            baseline_conversion_rate=None,  # Missing
            reported_p_value=0.03,
            reported_effect_size=0.05,
            test_timestamp=datetime(2023, 6, 15),
        )

        result = reconstruct_from_binary_summary(summary)

        # Should still succeed with fallback
        assert result.success or len(result.warning_messages) > 0
        assert 'FR-012' in ' '.join(result.warning_messages) or result.success

    def test_binary_summary_invalid_samples(self):
        """Test reconstruction with invalid sample sizes."""
        summary = ABTestSummary(
            source_url='https://example.com/test3',
            domain='tech',
            publication_year=2023,
            sample_size_control=0,
            sample_size_treatment=0,
            successes_control=0,
            successes_treatment=0,
            baseline_conversion_rate=0.20,
            reported_p_value=0.05,
            reported_effect_size=0.0,
            test_timestamp=datetime(2023, 6, 15),
        )

        result = reconstruct_from_binary_summary(summary)

        assert not result.success
        assert np.isnan(result.reconstructed_p_value)


class TestReconstructFromContinuousSummary:
    """Tests for continuous summary reconstruction."""

    def test_continuous_summary_reconstruction(self):
        """Test reconstruction from ABTestSummary with continuous outcome."""
        summary = ABTestSummary(
            source_url='https://example.com/test4',
            domain='ecommerce',
            publication_year=2023,
            sample_size_control=200,
            sample_size_treatment=200,
            mean_control=100.0,
            mean_treatment=105.0,
            std_control=15.0,
            std_treatment=15.0,
            reported_p_value=0.002,
            reported_effect_size=0.33,
            test_timestamp=datetime(2023, 6, 15),
        )

        result = reconstruct_from_continuous_summary(summary)

        assert result.success
        assert result.test_type == 'continuous_welch'
        assert not np.isnan(result.reconstructed_p_value)
        assert not np.isnan(result.reconstructed_effect_size)

    def test_continuous_summary_missing_means(self):
        """Test reconstruction when means are missing."""
        summary = ABTestSummary(
            source_url='https://example.com/test5',
            domain='ecommerce',
            publication_year=2023,
            sample_size_control=200,
            sample_size_treatment=200,
            mean_control=None,
            mean_treatment=None,
            std_control=15.0,
            std_treatment=15.0,
            reported_p_value=0.05,
            reported_effect_size=0.0,
            test_timestamp=datetime(2023, 6, 15),
        )

        result = reconstruct_from_continuous_summary(summary)

        assert not result.success
        assert len(result.warning_messages) > 0


class TestReconstructPValue:
    """Tests for main reconstruction dispatcher."""

    def test_binary_outcome_detection(self):
        """Test that binary outcomes are detected and processed correctly."""
        summary = ABTestSummary(
            source_url='https://example.com/test6',
            domain='tech',
            publication_year=2023,
            sample_size_control=1000,
            sample_size_treatment=1000,
            successes_control=200,
            successes_treatment=250,
            baseline_conversion_rate=0.20,
            reported_p_value=0.008,
            reported_effect_size=0.05,
            test_timestamp=datetime(2023, 6, 15),
        )

        result = reconstruct_p_value(summary)

        assert result.test_type in ['binary_z_test', 'binary_fisher']
        assert result.success

    def test_continuous_outcome_detection(self):
        """Test that continuous outcomes are detected and processed correctly."""
        summary = ABTestSummary(
            source_url='https://example.com/test7',
            domain='ecommerce',
            publication_year=2023,
            sample_size_control=200,
            sample_size_treatment=200,
            mean_control=100.0,
            mean_treatment=105.0,
            std_control=15.0,
            std_treatment=15.0,
            reported_p_value=0.002,
            reported_effect_size=0.33,
            test_timestamp=datetime(2023, 6, 15),
        )

        result = reconstruct_p_value(summary)

        assert result.test_type == 'continuous_welch'
        assert result.success


class TestValidateReconstruction:
    """Tests for reconstruction validation."""

    def test_valid_reconstruction(self):
        """Test validation passes for valid reconstruction."""
        result = ReconstructionResult(
            test_type='binary_z_test',
            reconstructed_p_value=0.045,
            reconstructed_effect_size=0.05,
            reported_p_value=0.048,
            reported_effect_size=0.052,
            absolute_p_difference=0.003,
            relative_effect_size_difference=0.04,
            success=True,
            warning_messages=[],
        )

        assert validate_reconstruction(result, p_threshold=0.05, effect_threshold=0.05)

    def test_invalid_p_difference(self):
        """Test validation fails when p-difference exceeds threshold."""
        result = ReconstructionResult(
            test_type='binary_z_test',
            reconstructed_p_value=0.10,
            reconstructed_effect_size=0.05,
            reported_p_value=0.03,
            reported_effect_size=0.05,
            absolute_p_difference=0.07,  # Exceeds 0.05
            relative_effect_size_difference=0.0,
            success=True,
            warning_messages=[],
        )

        assert not validate_reconstruction(result, p_threshold=0.05, effect_threshold=0.05)

    def test_invalid_effect_difference(self):
        """Test validation fails when effect-size difference exceeds threshold."""
        result = ReconstructionResult(
            test_type='binary_z_test',
            reconstructed_p_value=0.04,
            reconstructed_effect_size=0.10,
            reported_p_value=0.04,
            reported_effect_size=0.04,
            absolute_p_difference=0.0,
            relative_effect_size_difference=0.15,  # Exceeds 0.05
            success=True,
            warning_messages=[],
        )

        assert not validate_reconstruction(result, p_threshold=0.05, effect_threshold=0.05)

    def test_failed_reconstruction(self):
        """Test validation fails when reconstruction itself failed."""
        result = ReconstructionResult(
            test_type='binary_z_test',
            reconstructed_p_value=float('nan'),
            reconstructed_effect_size=float('nan'),
            reported_p_value=0.05,
            reported_effect_size=0.05,
            absolute_p_difference=float('nan'),
            relative_effect_size_difference=float('nan'),
            success=False,
            warning_messages=['Invalid sample sizes'],
        )

        assert not validate_reconstruction(result)


class TestReconstructorIntegration:
    """Integration tests for the reconstructor module."""

    def test_fixture_known_values(self):
        """Test against known fixture values for verification."""
        # Fixture: Control 1000 samples, 200 successes; Treatment 1000 samples, 250 successes
        summary = ABTestSummary(
            source_url='https://example.com/fixture1',
            domain='tech',
            publication_year=2023,
            sample_size_control=1000,
            sample_size_treatment=1000,
            successes_control=200,
            successes_treatment=250,
            baseline_conversion_rate=0.20,
            reported_p_value=0.008,
            reported_effect_size=0.05,
            test_timestamp=datetime(2023, 6, 15),
        )

        result = reconstruct_p_value(summary)

        # Verify reconstruction matches expected fixture values
        assert result.success
        assert result.reconstructed_effect_size == pytest.approx(0.05, rel=0.01)
        # P-value should be in reasonable range for this effect size
        assert 0 < result.reconstructed_p_value < 0.10

    def test_fixture_continuous_values(self):
        """Test continuous reconstruction against known fixture values."""
        summary = ABTestSummary(
            source_url='https://example.com/fixture2',
            domain='ecommerce',
            publication_year=2023,
            sample_size_control=200,
            sample_size_treatment=200,
            mean_control=100.0,
            mean_treatment=105.0,
            std_control=15.0,
            std_treatment=15.0,
            reported_p_value=0.002,
            reported_effect_size=0.33,
            test_timestamp=datetime(2023, 6, 15),
        )

        result = reconstruct_p_value(summary)

        assert result.success
        assert result.test_type == 'continuous_welch'
        assert not np.isnan(result.reconstructed_p_value)
        assert not np.isnan(result.reconstructed_effect_size)