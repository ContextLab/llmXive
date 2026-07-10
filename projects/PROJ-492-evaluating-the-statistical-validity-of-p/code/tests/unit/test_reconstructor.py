"""
Unit tests for T023: Statistical Reconstruction Module.
Verifies reconstructed values match known fixtures for z-test, Fisher, and Welch t-test.
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
    """Tests for two-proportion z-test reconstruction."""

    def test_known_fixture(self):
        """
        Fixture:
        Control: n=1000, x=100 (p=0.10)
        Treatment: n=1000, x=120 (p=0.12)
        Expected p-value ~ 0.14 (approx)
        """
        n_c, x_c = 1000, 100
        n_t, x_t = 1000, 120

        p_val, eff = reconstruct_binary_z_test(n_c, x_c, n_t, x_t)

        # Verify effect size
        assert abs(eff - 0.02) < 1e-6

        # Verify p-value is in reasonable range (not 0, not 1)
        assert 0.0 < p_val < 1.0
        
        # Manual check:
        # p_pooled = 0.11
        # se = sqrt(0.11*0.89*(2/1000)) = sqrt(0.0001958) = 0.01399
        # z = 0.02 / 0.01399 = 1.429
        # p = 2 * (1 - norm.cdf(1.429)) = 0.153
        expected_p = 2 * (1 - stats.norm.cdf(abs(0.02 / np.sqrt(0.11 * 0.89 * (2/1000)))))
        assert abs(p_val - expected_p) < 1e-4

    def test_identical_proportions(self):
        """If proportions are identical, p-value should be 1.0."""
        p_val, eff = reconstruct_binary_z_test(100, 10, 100, 10)
        assert abs(eff) < 1e-9
        assert abs(p_val - 1.0) < 1e-6

    def test_zero_successes(self):
        """Handle case where both groups have zero successes."""
        p_val, eff = reconstruct_binary_z_test(100, 0, 100, 0)
        assert abs(p_val - 1.0) < 1e-6
        assert abs(eff) < 1e-9


class TestBinaryFisherTest:
    """Tests for Fisher's Exact Test reconstruction."""

    def test_known_fixture(self):
        """
        Fixture:
        Control: n=20, x=5
        Treatment: n=20, x=15
        Table: [[5, 15], [15, 5]]
        """
        n_c, x_c = 20, 5
        n_t, x_t = 20, 15

        p_val, eff = reconstruct_binary_fisher_test(n_c, x_c, n_t, x_t)

        # Manual check using scipy directly
        table = [[5, 15], [15, 5]]
        _, expected_p = stats.fisher_exact(table, alternative='two-sided')
        
        assert abs(p_val - expected_p) < 1e-6
        assert abs(eff - 0.5) < 1e-6 # (15/20 - 5/20) = 0.5

    def test_small_sample_significant(self):
        """Small sample with large difference should be significant."""
        # Control: 0/10, Treatment: 10/10
        p_val, _ = reconstruct_binary_fisher_test(10, 0, 10, 10)
        assert p_val < 0.01 # Should be very small

    def test_degenerate_table(self):
        """Handle case where table is all zeros (edge case)."""
        # This should not crash, but return p=1.0 as per implementation
        p_val, eff = reconstruct_binary_fisher_test(10, 0, 10, 0)
        assert abs(p_val - 1.0) < 1e-6


class TestWelchTTest:
    """Tests for Welch's t-test reconstruction."""

    def test_known_fixture(self):
        """
        Fixture:
        Control: n=30, mean=10, std=2
        Treatment: n=30, mean=12, std=2.5
        """
        n_c, m_c, s_c = 30, 10.0, 2.0
        n_t, m_t, s_t = 30, 12.0, 2.5

        p_val, eff = reconstruct_continuous_welch_t_test(n_c, m_c, s_c, n_t, m_t, s_t)

        # Manual check
        se = np.sqrt((s_c**2/n_c) + (s_t**2/n_t))
        t_stat = (m_t - m_c) / se
        # df approx
        num = (s_c**2/n_c + s_t**2/n_t)**2
        denom = ((s_c**2/n_c)**2/(n_c-1)) + ((s_t**2/n_t)**2/(n_t-1))
        df = num / denom
        expected_p = 2 * (1 - stats.t.cdf(abs(t_stat), df))

        assert abs(p_val - expected_p) < 1e-4
        assert abs(eff - 2.0) < 1e-6

    def test_identical_means(self):
        """If means are identical, p-value should be 1.0."""
        p_val, eff = reconstruct_continuous_welch_t_test(30, 10.0, 2.0, 30, 10.0, 2.5)
        assert abs(eff) < 1e-9
        assert abs(p_val - 1.0) < 1e-6

    def test_zero_std(self):
        """Handle zero standard deviation."""
        # If std is 0 and means differ, p should be 0.
        p_val, eff = reconstruct_continuous_welch_t_test(10, 5.0, 0.0, 10, 6.0, 0.0)
        assert p_val == 0.0
        assert abs(eff - 1.0) < 1e-6

        # If std is 0 and means same, p should be 1.
        p_val, eff = reconstruct_continuous_welch_t_test(10, 5.0, 0.0, 10, 5.0, 0.0)
        assert abs(p_val - 1.0) < 1e-6


class TestReconstructSingleSummary:
    """Tests for the high-level reconstruction function."""

    def test_binary_summary(self):
        summary = ABTestSummary(
            id="test-001",
            url="http://example.com",
            domain="example.com",
            test_type="binary",
            n_control=1000,
            n_treatment=1000,
            x_control=100,
            x_treatment=120,
            conversion_rate_control=0.10,
            conversion_rate_treatment=0.12,
            mean_control=None,
            mean_treatment=None,
            std_control=None,
            std_treatment=None
        )
        res = reconstruct_single_summary(summary)
        assert res['reconstructed_p_value'] is not None
        assert res['reconstructed_effect_size'] is not None
        assert res['method'] in ['z_test_binary', 'fisher_exact']
        assert res['error'] is None

    def test_continuous_summary(self):
        summary = ABTestSummary(
            id="test-002",
            url="http://example.com/2",
            domain="example.com",
            test_type="continuous",
            n_control=30,
            n_treatment=30,
            x_control=None,
            x_treatment=None,
            conversion_rate_control=None,
            conversion_rate_treatment=None,
            mean_control=10.0,
            mean_treatment=12.0,
            std_control=2.0,
            std_treatment=2.5
        )
        res = reconstruct_single_summary(summary)
        assert res['reconstructed_p_value'] is not None
        assert res['reconstructed_effect_size'] is not None
        assert res['method'] == 'welch_t_test'
        assert res['error'] is None

    def test_missing_data(self):
        """Test fallback or error handling for missing data."""
        summary = ABTestSummary(
            id="test-003",
            url="http://example.com/3",
            domain="example.com",
            test_type="binary",
            n_control=1000,
            n_treatment=1000,
            x_control=None,
            x_treatment=None,
            conversion_rate_control=None,
            conversion_rate_treatment=None,
            mean_control=None,
            mean_treatment=None,
            std_control=None,
            std_treatment=None
        )
        res = reconstruct_single_summary(summary)
        assert res['error'] is not None
        assert "Missing" in res['error']