"""
Unit tests for the statistical reconstruction module.
Verifies that reconstructed values match known fixtures for Z-test, Fisher's, and Welch's T-test.
"""

import pytest
import numpy as np
from scipy import stats

from code.src.audit.reconstructor import (
    reconstruct_binary_z_test,
    reconstruct_binary_fisher_test,
    reconstruct_continuous_welch_t_test,
    reconstruct_single_summary
)
from code.src.models.data_models import ABTestSummary


class TestBinaryZTest:
    def test_reconstruct_z_test_known_values(self):
        """
        Test Z-test reconstruction with known values.
        Control: 1000 samples, 100 successes (10%)
        Treatment: 1000 samples, 120 successes (12%)
        Expected p-value should be small (< 0.05)
        """
        n_control = 1000
        n_treatment = 1000
        x_control = 100
        x_treatment = 120

        p_value, effect_size = reconstruct_binary_z_test(n_control, n_treatment, x_control, x_treatment)

        # Verify effect size
        expected_effect = 0.12 - 0.10
        assert abs(effect_size - expected_effect) < 1e-6

        # Verify p-value is reasonable (not 0 or 1 for this effect)
        assert 0.0 < p_value < 1.0
        # Manually calculate expected p-value for verification
        # Pooled p = 0.11
        # SE = sqrt(0.11 * 0.89 * (2/1000)) = sqrt(0.0001958) = 0.01399
        # Z = 0.02 / 0.01399 = 1.429
        # p = 2 * (1 - norm.cdf(1.429)) = 0.153
        assert abs(p_value - 0.153) < 0.01  # Allow small tolerance

    def test_z_test_identical_proportions(self):
        """Test that identical proportions yield p=1.0"""
        p_value, effect_size = reconstruct_binary_z_test(100, 100, 50, 50)
        assert p_value == 1.0
        assert effect_size == 0.0

    def test_z_test_small_sample(self):
        """Test Z-test with small sample sizes"""
        p_value, effect_size = reconstruct_binary_z_test(10, 10, 2, 8)
        # Should not raise an error
        assert 0.0 <= p_value <= 1.0


class TestBinaryFisherTest:
    def test_reconstruct_fisher_known_values(self):
        """
        Test Fisher's Exact test with known values.
        Table: [[1, 9], [9, 1]] (Strong effect)
        """
        n_control = 10
        n_treatment = 10
        x_control = 1
        x_treatment = 9

        p_value, effect_size = reconstruct_binary_fisher_test(n_control, n_treatment, x_control, x_treatment)

        # Verify effect size
        expected_effect = 0.9 - 0.1
        assert abs(effect_size - expected_effect) < 1e-6

        # Fisher's exact for [[1,9],[9,1]] should be very small
        assert p_value < 0.01

    def test_fisher_identical(self):
        """Test Fisher's with identical proportions"""
        p_value, effect_size = reconstruct_binary_fisher_test(10, 10, 5, 5)
        assert p_value == 1.0
        assert effect_size == 0.0


class TestWelchTTest:
    def test_reconstruct_welch_known_values(self):
        """
        Test Welch's T-test with known values.
        Control: n=100, mean=50, std=10
        Treatment: n=100, mean=55, std=12
        """
        n_control = 100
        mean_control = 50.0
        std_control = 10.0
        n_treatment = 100
        mean_treatment = 55.0
        std_treatment = 12.0

        p_value, effect_size = reconstruct_continuous_welch_t_test(
            n_control, mean_control, std_control,
            n_treatment, mean_treatment, std_treatment
        )

        # Verify p-value is not 0 or 1 for this effect
        assert 0.0 < p_value < 1.0
        # Effect size should be negative (treatment - control) -> 55-50=5? No, treatment is 55, control 50.
        # Wait, treatment mean is 55, control is 50. So effect is positive.
        assert effect_size > 0

    def test_welch_identical(self):
        """Test Welch's with identical means and stds"""
        p_value, effect_size = reconstruct_continuous_welch_t_test(
            100, 50.0, 10.0, 100, 50.0, 10.0
        )
        assert p_value == 1.0
        assert effect_size == 0.0

    def test_welch_zero_std(self):
        """Test Welch's with zero standard deviation"""
        # If both stds are 0 and means differ, effect is infinite
        p_value, effect_size = reconstruct_continuous_welch_t_test(
            10, 50.0, 0.0, 10, 60.0, 0.0
        )
        assert p_value == 0.0
        assert effect_size == float('inf')


class TestReconstructSingleSummary:
    def test_reconstruct_binary_summary(self):
        """Test full reconstruction of a binary summary"""
        summary = ABTestSummary(
            url="http://example.com/test1",
            source_id="src_001",
            outcome_type="binary",
            control_n=1000,
            control_rate=0.10,
            treatment_n=1000,
            treatment_rate=0.12,
            domain="tech",
            year=2023
        )

        result = reconstruct_single_summary(summary)

        assert result['status'] == 'success'
        assert result['test_type'] in ['z_test', 'fisher']
        assert 0.0 < result['reconstructed_p_value'] < 1.0
        assert result['reconstructed_effect_size'] > 0

    def test_reconstruct_continuous_summary(self):
        """Test full reconstruction of a continuous summary"""
        summary = ABTestSummary(
            url="http://example.com/test2",
            source_id="src_002",
            outcome_type="continuous",
            control_n=100,
            control_mean=50.0,
            control_std=10.0,
            treatment_n=100,
            treatment_mean=55.0,
            treatment_std=12.0,
            domain="tech",
            year=2023
        )

        result = reconstruct_single_summary(summary)

        assert result['status'] == 'success'
        assert result['test_type'] == 'welch_t'
        assert 0.0 < result['reconstructed_p_value'] < 1.0

    def test_reconstruct_missing_data_fallback(self):
        """Test that missing data triggers fallback"""
        summary = ABTestSummary(
            url="http://example.com/test3",
            source_id="src_003",
            outcome_type="binary",
            control_n=1000,
            control_rate=None,  # Missing
            treatment_n=1000,
            treatment_rate=0.12,
            domain="tech",
            year=2023
        )

        result = reconstruct_single_summary(summary)

        assert result['status'] == 'failed'
        assert result['test_type'] == 'fallback'
        assert result['reconstructed_p_value'] is None