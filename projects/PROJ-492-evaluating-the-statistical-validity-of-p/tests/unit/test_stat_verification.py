"""
Unit tests for statistical verification utilities.

Tests verify that z-test, t-test, and Fisher's exact test
functions compute correct values and handle edge cases.
"""

import pytest
import numpy as np
from src.audit.stat_verification import (
    two_proportion_ztest,
    welch_ttest,
    fisher_exact_test,
    verify_ztest,
    verify_ttest,
    verify_fisher,
    run_all_verifications
)


class TestTwoProportionZTest:
    """Tests for two-proportion z-test function."""

    def test_identical_proportions(self):
        """Test with identical proportions should give p=1."""
        z_stat, p_value = two_proportion_ztest(100, 50, 100, 50)
        assert z_stat == 0.0
        assert p_value == 1.0

    def test_different_proportions(self):
        """Test with different proportions should give p<1."""
        z_stat, p_value = two_proportion_ztest(1000, 500, 1000, 520)
        assert z_stat != 0.0
        assert 0 < p_value < 1

    def test_invalid_sample_size(self):
        """Test that invalid sample sizes raise ValueError."""
        with pytest.raises(ValueError):
            two_proportion_ztest(0, 0, 100, 50)

    def test_invalid_success_count(self):
        """Test that invalid success counts raise ValueError."""
        with pytest.raises(ValueError):
            two_proportion_ztest(100, 150, 100, 50)

    def test_return_types(self):
        """Test that return values are floats."""
        z_stat, p_value = two_proportion_ztest(100, 50, 100, 60)
        assert isinstance(z_stat, float)
        assert isinstance(p_value, float)


class TestWelchTTest:
    """Tests for Welch's t-test function."""

    def test_identical_means(self):
        """Test with identical means should give p=1."""
        t_stat, p_value = welch_ttest(10.0, 10.0, 3.0, 3.0, 100, 100)
        assert t_stat == 0.0
        assert p_value == 1.0

    def test_different_means(self):
        """Test with different means should give p<1."""
        t_stat, p_value = welch_ttest(10.0, 12.0, 3.0, 3.0, 100, 100)
        assert t_stat != 0.0
        assert 0 < p_value < 1

    def test_unequal_variances(self):
        """Test with unequal variances."""
        t_stat, p_value = welch_ttest(10.0, 12.0, 2.0, 4.0, 100, 100)
        assert t_stat != 0.0
        assert 0 < p_value < 1

    def test_invalid_sample_size(self):
        """Test that sample size < 2 raises ValueError."""
        with pytest.raises(ValueError):
            welch_ttest(10.0, 12.0, 3.0, 3.0, 1, 1)

    def test_invalid_std(self):
        """Test that negative std raises ValueError."""
        with pytest.raises(ValueError):
            welch_ttest(10.0, 12.0, -3.0, 3.0, 100, 100)

    def test_return_types(self):
        """Test that return values are floats."""
        t_stat, p_value = welch_ttest(10.0, 12.0, 3.0, 3.0, 100, 100)
        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)


class TestFisherExactTest:
    """Tests for Fisher's exact test function."""

    def test_balanced_table(self):
        """Test with balanced 2x2 table."""
        odds_ratio, p_value = fisher_exact_test(10, 10, 10, 10)
        assert p_value == 1.0  # Perfectly balanced

    def test_imbalanced_table(self):
        """Test with imbalanced table."""
        odds_ratio, p_value = fisher_exact_test(10, 20, 30, 10)
        assert 0 <= p_value <= 1
        assert odds_ratio > 0

    def test_small_counts(self):
        """Test with small cell counts."""
        odds_ratio, p_value = fisher_exact_test(1, 2, 3, 4)
        assert 0 <= p_value <= 1
        assert odds_ratio > 0

    def test_invalid_counts(self):
        """Test that negative counts raise ValueError."""
        with pytest.raises(ValueError):
            fisher_exact_test(-1, 2, 3, 4)

    def test_return_types(self):
        """Test that return values are floats."""
        odds_ratio, p_value = fisher_exact_test(10, 20, 15, 15)
        assert isinstance(odds_ratio, float)
        assert isinstance(p_value, float)


class TestVerificationFunctions:
    """Tests for verification utility functions."""

    def test_verify_ztest(self):
        """Test z-test verification returns expected structure."""
        result = verify_ztest()
        assert "test" in result
        assert "passed" in result
        assert "z_statistic" in result
        assert "p_value" in result
        assert result["test"] == "z-test"

    def test_verify_ttest(self):
        """Test t-test verification returns expected structure."""
        result = verify_ttest()
        assert "test" in result
        assert "passed" in result
        assert "t_statistic" in result
        assert "p_value" in result
        assert result["test"] == "Welch t-test"

    def test_verify_fisher(self):
        """Test Fisher verification returns expected structure."""
        result = verify_fisher()
        assert "test" in result
        assert "passed" in result
        assert "odds_ratio" in result
        assert "p_value" in result
        assert result["test"] == "Fisher's exact test"

    def test_run_all_verifications(self):
        """Test that all verifications run and return dict."""
        results = run_all_verifications()
        assert "ztest" in results
        assert "ttest" in results
        assert "fisher" in results
        assert isinstance(results["ztest"], bool)
        assert isinstance(results["ttest"], bool)
        assert isinstance(results["fisher"], bool)
        assert all(results.values())  # All should pass
