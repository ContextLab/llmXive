import pytest
import numpy as np
from code.analysis.stats import apply_bonferroni_correction

class TestBonferroniCorrection:
    """Unit tests for Bonferroni correction application."""

    def test_bonferroni_single_test(self):
        """Test Bonferroni correction with a single hypothesis test."""
        p_value = 0.05
        corrected_p, is_significant = apply_bonferroni_correction(p_value, n_tests=1, alpha=0.05)
        assert corrected_p == pytest.approx(0.05)
        assert is_significant is True

    def test_bonferroni_multiple_tests(self):
        """Test Bonferroni correction with multiple hypothesis tests."""
        p_value = 0.01
        n_tests = 5
        expected_corrected = 0.05
        corrected_p, is_significant = apply_bonferroni_correction(p_value, n_tests=n_tests, alpha=0.05)
        assert corrected_p == pytest.approx(expected_corrected)
        assert is_significant is True

    def test_bonferroni_non_significant(self):
        """Test that Bonferroni correction correctly marks non-significant results."""
        p_value = 0.02
        n_tests = 10
        # 0.02 * 10 = 0.2, which is > 0.05
        corrected_p, is_significant = apply_bonferroni_correction(p_value, n_tests=n_tests, alpha=0.05)
        assert corrected_p == pytest.approx(0.2)
        assert is_significant is False

    def test_bonferroni_cap_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        p_value = 0.9
        n_tests = 2
        # 0.9 * 2 = 1.8, should be capped at 1.0
        corrected_p, is_significant = apply_bonferroni_correction(p_value, n_tests=n_tests, alpha=0.05)
        assert corrected_p == pytest.approx(1.0)
        assert is_significant is False

    def test_bonferroni_zero_tests_raises(self):
        """Test that zero tests raises a ValueError."""
        with pytest.raises(ValueError, match="Number of tests must be at least 1"):
            apply_bonferroni_correction(0.05, n_tests=0)

    def test_bonferroni_negative_p_raises(self):
        """Test that negative p-values raise a ValueError."""
        with pytest.raises(ValueError, match="p-value must be between 0 and 1"):
            apply_bonferroni_correction(-0.1, n_tests=5)

    def test_bonferroni_p_greater_than_one_raises(self):
        """Test that p-values > 1 raise a ValueError."""
        with pytest.raises(ValueError, match="p-value must be between 0 and 1"):
            apply_bonferroni_correction(1.5, n_tests=5)

    def test_bonferroni_edge_case_p_zero(self):
        """Test behavior when p-value is exactly 0."""
        corrected_p, is_significant = apply_bonferroni_correction(0.0, n_tests=10, alpha=0.05)
        assert corrected_p == pytest.approx(0.0)
        assert is_significant is True

    def test_bonferroni_edge_case_p_one(self):
        """Test behavior when p-value is exactly 1."""
        corrected_p, is_significant = apply_bonferroni_correction(1.0, n_tests=1, alpha=0.05)
        assert corrected_p == pytest.approx(1.0)
        assert is_significant is False
