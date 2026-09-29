import pytest
import numpy as np
from code.analysis.stats import apply_bonferroni_correction
from code.processing.shape_metrics import bin_halo_by_shape

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


class TestShapeBinningLogic:
    """Unit tests for binning logic (prolate/triaxial/spherical) in shape_metrics."""

    def test_bin_halo_c_a_less_than_0_5_prolate(self):
        """Test that c/a < 0.5 is classified as 'prolate'."""
        # c/a = 0.4 -> prolate
        result = bin_halo_by_shape(c_a_ratio=0.4, b_a_ratio=0.6)
        assert result == 'prolate'

    def test_bin_halo_c_a_between_0_5_and_0_8_triaxial(self):
        """Test that 0.5 <= c/a <= 0.8 is classified as 'triaxial'."""
        # Lower bound
        result = bin_halo_by_shape(c_a_ratio=0.5, b_a_ratio=0.6)
        assert result == 'triaxial'

        # Upper bound
        result = bin_halo_by_shape(c_a_ratio=0.8, b_a_ratio=0.6)
        assert result == 'triaxial'

        # Middle
        result = bin_halo_by_shape(c_a_ratio=0.65, b_a_ratio=0.6)
        assert result == 'triaxial'

    def test_bin_halo_c_a_greater_than_0_8_spherical(self):
        """Test that c/a > 0.8 is classified as 'spherical'."""
        # c/a = 0.85 -> spherical
        result = bin_halo_by_shape(c_a_ratio=0.85, b_a_ratio=0.9)
        assert result == 'spherical'

    def test_bin_halo_c_a_exactly_0_5(self):
        """Test boundary condition where c/a is exactly 0.5."""
        # According to logic: if c/a < 0.5 -> prolate, else if c/a <= 0.8 -> triaxial
        # So 0.5 falls into triaxial
        result = bin_halo_by_shape(c_a_ratio=0.5, b_a_ratio=0.5)
        assert result == 'triaxial'

    def test_bin_halo_c_a_exactly_0_8(self):
        """Test boundary condition where c/a is exactly 0.8."""
        # According to logic: if c/a <= 0.8 -> triaxial, else -> spherical
        # So 0.8 falls into triaxial
        result = bin_halo_by_shape(c_a_ratio=0.8, b_a_ratio=0.8)
        assert result == 'triaxial'

    def test_bin_halo_invalid_ratios(self):
        """Test behavior with invalid input ratios (should still bin based on value)."""
        # Even if b_a_ratio is invalid, the function should still return a bin based on c_a_ratio
        # Note: This assumes the function validates inputs elsewhere or handles them gracefully
        # We test the binning logic specifically
        result = bin_halo_by_shape(c_a_ratio=0.3, b_a_ratio=1.5)
        assert result == 'prolate'

    def test_bin_halo_edge_case_c_a_zero(self):
        """Test binning when c/a is 0 (extreme prolate)."""
        result = bin_halo_by_shape(c_a_ratio=0.0, b_a_ratio=0.5)
        assert result == 'prolate'

    def test_bin_halo_edge_case_c_a_one(self):
        """Test binning when c/a is 1 (perfectly spherical)."""
        result = bin_halo_by_shape(c_a_ratio=1.0, b_a_ratio=1.0)
        assert result == 'spherical'