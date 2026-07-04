"""
Unit tests for statistical verification utilities in stat_verification.py.
"""

import pytest
import numpy as np
from scipy import stats

from code.src.audit.stat_verification import (
    two_proportion_z_test,
    welch_t_test,
    fisher_exact_test,
    verify_z_test_consistency,
    verify_welch_t_consistency,
    verify_fisher_consistency
)


class TestTwoProportionZTest:
    def test_basic_binary_case(self):
        """Test a standard case where we know the expected result."""
        # Group 1: 100 successes out of 1000 (10%)
        # Group 2: 120 successes out of 1000 (12%)
        n1, x1 = 1000, 100
        n2, x2 = 1000, 120

        z, p = two_proportion_z_test(n1, x1, n2, x2)

        # Manual calculation check
        p1, p2 = 0.1, 0.12
        p_pooled = (100 + 120) / (1000 + 1000)
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/1000 + 1/1000))
        expected_z = (p1 - p2) / se
        expected_p = 2 * (1 - stats.norm.cdf(abs(expected_z)))

        assert np.isclose(z, expected_z, rtol=1e-5)
        assert np.isclose(p, expected_p, rtol=1e-5)

    def test_identical_proportions(self):
        """Test when proportions are identical, p-value should be 1.0."""
        n1, x1 = 1000, 100
        n2, x2 = 1000, 100

        z, p = two_proportion_z_test(n1, x1, n2, x2)

        assert np.isclose(z, 0.0)
        assert np.isclose(p, 1.0)

    def test_zero_successes(self):
        """Test with zero successes in both groups."""
        n1, x1 = 500, 0
        n2, x2 = 500, 0

        z, p = two_proportion_z_test(n1, x1, n2, x2)
        assert np.isclose(z, 0.0)
        assert np.isclose(p, 1.0)

    def test_invalid_sample_size(self):
        """Test that negative or zero sample size raises error."""
        with pytest.raises(ValueError):
            two_proportion_z_test(0, 0, 100, 10)
        with pytest.raises(ValueError):
            two_proportion_z_test(-10, 0, 100, 10)


class TestWelchTTest:
    def test_basic_continuous_case(self):
        """Test a standard continuous case."""
        # Group 1: mean=10, std=2, n=50
        # Group 2: mean=12, std=2.5, n=60
        mean1, std1, n1 = 10.0, 2.0, 50
        mean2, std2, n2 = 12.0, 2.5, 60

        t, p = welch_t_test(mean1, mean2, std1, std2, n1, n2)

        # Manual check
        # t = (mean1 - mean2) / sqrt(s1^2/n1 + s2^2/n2)
        denominator = np.sqrt((std1**2 / n1) + (std2**2 / n2))
        expected_t = (mean1 - mean2) / denominator

        # Degrees of freedom
        num = (std1**2/n1 + std2**2/n2)**2
        denom = (std1**2/n1)**2/(n1-1) + (std2**2/n2)**2/(n2-1)
        expected_df = num / denom

        expected_p = 2 * stats.t.sf(abs(expected_t), expected_df)

        assert np.isclose(t, expected_t, rtol=1e-5)
        assert np.isclose(p, expected_p, rtol=1e-5)

    def test_identical_means(self):
        """Test when means are identical, p-value should be 1.0."""
        t, p = welch_t_test(10.0, 10.0, 2.0, 2.0, 50, 50)
        assert np.isclose(t, 0.0)
        assert np.isclose(p, 1.0)

    def test_zero_std_both(self):
        """Test when both stds are zero and means are equal."""
        t, p = welch_t_test(10.0, 10.0, 0.0, 0.0, 50, 50)
        assert np.isclose(t, 0.0)
        assert np.isclose(p, 1.0)

    def test_zero_std_different_means(self):
        """Test when both stds are zero but means differ."""
        t, p = welch_t_test(10.0, 12.0, 0.0, 0.0, 50, 50)
        assert t == float('inf')
        assert p == 0.0

    def test_invalid_sample_size(self):
        """Test that negative or zero sample size raises error."""
        with pytest.raises(ValueError):
            welch_t_test(10.0, 12.0, 2.0, 2.0, 0, 50)
        with pytest.raises(ValueError):
            welch_t_test(10.0, 12.0, 2.0, 2.0, 50, -5)


class TestFisherExactTest:
    def test_basic_2x2(self):
        """Test a basic 2x2 table."""
        # Table: [[10, 90], [20, 80]] -> Group 1: 10/100, Group 2: 20/100
        n1, x1 = 100, 10
        n2, x2 = 100, 20

        odds_ratio, p = fisher_exact_test(n1, x1, n2, x2)

        # Verify against scipy directly
        table = [[10, 90], [20, 80]]
        expected_or, expected_p = stats.fisher_exact(table, alternative='two-sided')

        assert np.isclose(odds_ratio, expected_or)
        assert np.isclose(p, expected_p)

    def test_identical_rates(self):
        """Test when success rates are identical."""
        n1, x1 = 100, 10
        n2, x2 = 100, 10

        odds_ratio, p = fisher_exact_test(n1, x1, n2, x2)

        # Odds ratio should be 1.0
        assert np.isclose(odds_ratio, 1.0)
        # P-value should be 1.0
        assert np.isclose(p, 1.0)

    def test_invalid_input(self):
        """Test invalid inputs."""
        with pytest.raises(ValueError):
            fisher_exact_test(0, 0, 100, 10)
        with pytest.raises(ValueError):
            fisher_exact_test(100, 110, 100, 10) # x1 > n1


class TestVerificationWrappers:
    def test_z_test_consistency_true(self):
        """Test verification when difference is within threshold."""
        n1, x1, n2, x2 = 1000, 100, 1000, 120
        _, true_p = two_proportion_z_test(n1, x1, n2, x2)
        
        # Use true p as reported
        result = verify_z_test_consistency(n1, x1, n2, x2, true_p, threshold=0.05)
        
        assert result['is_consistent'] is True
        assert result['absolute_difference'] <= 0.05

    def test_z_test_consistency_false(self):
        """Test verification when difference exceeds threshold."""
        n1, x1, n2, x2 = 1000, 100, 1000, 120
        _, true_p = two_proportion_z_test(n1, x1, n2, x2)
        
        # Use a reported p that is far off
        result = verify_z_test_consistency(n1, x1, n2, x2, 0.99, threshold=0.05)
        
        assert result['is_consistent'] is False
        assert result['absolute_difference'] > 0.05

    def test_welch_t_consistency(self):
        """Test Welch t-test verification."""
        mean1, mean2, std1, std2, n1, n2 = 10.0, 12.0, 2.0, 2.5, 50, 60
        _, true_p = welch_t_test(mean1, mean2, std1, std2, n1, n2)
        
        result = verify_welch_t_consistency(
            mean1, mean2, std1, std2, n1, n2, true_p, threshold=0.05
        )
        
        assert result['is_consistent'] is True

    def test_fisher_consistency(self):
        """Test Fisher exact test verification."""
        n1, x1, n2, x2 = 100, 10, 100, 20
        _, true_p = fisher_exact_test(n1, x1, n2, x2)
        
        result = verify_fisher_consistency(n1, x1, n2, x2, true_p, threshold=0.05)
        
        assert result['is_consistent'] is True