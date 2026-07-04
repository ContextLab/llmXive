"""
Unit tests for Spearman correlation calculation bounds.
Tests the statistical analysis module to ensure correlation coefficients
and p-values remain within mathematically valid ranges.
"""
import pytest
import numpy as np
from scipy.stats import spearmanr
from src.analysis.correlation import calculate_spearman_correlation


class TestSpearmanCorrelationBounds:
    """Test that Spearman correlation results are within valid bounds."""

    def test_correlation_coefficient_range(self):
        """Test that Spearman rho is always in [-1, 1]."""
        # Generate random data
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)

        rho, p_value = calculate_spearman_correlation(x, y)

        assert -1.0 <= rho <= 1.0, f"Correlation coefficient {rho} out of bounds [-1, 1]"

    def test_p_value_range(self):
        """Test that p-value is always in [0, 1]."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)

        rho, p_value = calculate_spearman_correlation(x, y)

        assert 0.0 <= p_value <= 1.0, f"P-value {p_value} out of bounds [0, 1]"

    def test_perfect_positive_correlation(self):
        """Test that perfectly correlated data gives rho ≈ 1."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # Perfect positive linear relationship

        rho, p_value = calculate_spearman_correlation(x, y)

        assert rho == 1.0, f"Expected rho=1.0 for perfect positive correlation, got {rho}"
        assert p_value == 0.0, f"Expected p=0.0 for perfect correlation, got {p_value}"

    def test_perfect_negative_correlation(self):
        """Test that perfectly anti-correlated data gives rho ≈ -1."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 4, 3, 2, 1])  # Perfect negative linear relationship

        rho, p_value = calculate_spearman_correlation(x, y)

        assert rho == -1.0, f"Expected rho=-1.0 for perfect negative correlation, got {rho}"
        assert p_value == 0.0, f"Expected p=0.0 for perfect correlation, got {p_value}"

    def test_no_correlation(self):
        """Test that uncorrelated random data gives rho ≈ 0."""
        np.random.seed(123)
        x = np.random.randn(1000)
        y = np.random.randn(1000)

        rho, p_value = calculate_spearman_correlation(x, y)

        # With large sample, rho should be close to 0
        assert abs(rho) < 0.1, f"Expected rho near 0 for uncorrelated data, got {rho}"
        assert p_value > 0.05, f"Expected p > 0.05 for uncorrelated data, got {p_value}"

    def test_single_value_edge_case(self):
        """Test behavior with single data point (should handle gracefully)."""
        x = np.array([1.0])
        y = np.array([2.0])

        # This should raise a warning or return NaN, not crash
        with pytest.warns(UserWarning):
            rho, p_value = calculate_spearman_correlation(x, y)
            # Result should be NaN or handled gracefully
            assert np.isnan(rho) or (0.0 <= p_value <= 1.0)

    def test_constant_array(self):
        """Test behavior when one variable is constant (undefined correlation)."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 2.0, 2.0, 2.0, 2.0])  # Constant

        # Should handle gracefully (NaN or warning)
        with pytest.warns(UserWarning):
            rho, p_value = calculate_spearman_correlation(x, y)
            assert np.isnan(rho) or (0.0 <= p_value <= 1.0)

    def test_empty_arrays(self):
        """Test behavior with empty input arrays."""
        x = np.array([])
        y = np.array([])

        with pytest.raises(ValueError):
            calculate_spearman_correlation(x, y)

    def test_mismatched_lengths(self):
        """Test behavior with mismatched array lengths."""
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([1.0, 2.0])

        with pytest.raises(ValueError):
            calculate_spearman_correlation(x, y)

    def test_with_nan_values(self):
        """Test behavior with NaN values in input."""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])

        # Should either raise error or handle NaN appropriately
        with pytest.raises((ValueError, RuntimeWarning)):
            calculate_spearman_correlation(x, y)

    def test_large_dataset_bounds(self):
        """Test bounds with large dataset to ensure numerical stability."""
        np.random.seed(456)
        x = np.random.randn(10000)
        y = np.random.randn(10000)

        rho, p_value = calculate_spearman_correlation(x, y)

        assert -1.0 <= rho <= 1.0, f"Large dataset rho {rho} out of bounds"
        assert 0.0 <= p_value <= 1.0, f"Large dataset p-value {p_value} out of bounds"

    def test_monotonic_relationship(self):
        """Test with monotonic but non-linear relationship."""
        x = np.linspace(0, 10, 100)
        y = x ** 2  # Monotonic increasing

        rho, p_value = calculate_spearman_correlation(x, y)

        assert rho == 1.0, f"Expected rho=1.0 for monotonic relationship, got {rho}"
        assert p_value == 0.0, f"Expected p=0.0 for monotonic relationship, got {p_value}"

    def test_non_monotonic_relationship(self):
        """Test with non-monotonic relationship (parabola)."""
        x = np.linspace(-5, 5, 100)
        y = x ** 2  # Non-monotonic (U-shaped)

        rho, p_value = calculate_spearman_correlation(x, y)

        # Spearman should detect no monotonic correlation
        assert abs(rho) < 0.1, f"Expected near-zero rho for non-monotonic, got {rho}"

    def test_outliers_impact(self):
        """Test that outliers don't break bounds (robustness check)."""
        x = np.array([1, 2, 3, 4, 5, 1000])  # Outlier
        y = np.array([2, 4, 6, 8, 10, 12])

        rho, p_value = calculate_spearman_correlation(x, y)

        # Should still be within bounds
        assert -1.0 <= rho <= 1.0, f"Outlier case rho {rho} out of bounds"
        assert 0.0 <= p_value <= 1.0, f"Outlier case p-value {p_value} out of bounds"

    def test_integer_input(self):
        """Test with integer arrays (not just floats)."""
        x = np.array([1, 2, 3, 4, 5], dtype=int)
        y = np.array([2, 4, 6, 8, 10], dtype=int)

        rho, p_value = calculate_spearman_correlation(x, y)

        assert rho == 1.0, f"Integer input failed: expected rho=1.0, got {rho}"
        assert p_value == 0.0, f"Integer input failed: expected p=0.0, got {p_value}"

    def test_float_input(self):
        """Test with float arrays."""
        x = np.array([1.5, 2.5, 3.5, 4.5, 5.5], dtype=float)
        y = np.array([2.5, 4.5, 6.5, 8.5, 10.5], dtype=float)

        rho, p_value = calculate_spearman_correlation(x, y)

        assert rho == 1.0, f"Float input failed: expected rho=1.0, got {rho}"
        assert p_value == 0.0, f"Float input failed: expected p=0.0, got {p_value}"

    def test_negative_values(self):
        """Test with negative values in input."""
        x = np.array([-5, -3, -1, 1, 3])
        y = np.array([-10, -6, -2, 2, 6])

        rho, p_value = calculate_spearman_correlation(x, y)

        assert rho == 1.0, f"Negative values failed: expected rho=1.0, got {rho}"
        assert p_value == 0.0, f"Negative values failed: expected p=0.0, got {p_value}"

    def test_mixed_sign_values(self):
        """Test with mixed positive and negative values."""
        x = np.array([-5, -2, 0, 2, 5])
        y = np.array([-10, -4, 0, 4, 10])

        rho, p_value = calculate_spearman_correlation(x, y)

        assert rho == 1.0, f"Mixed sign failed: expected rho=1.0, got {rho}"
        assert p_value == 0.0, f"Mixed sign failed: expected p=0.0, got {p_value}"

    def test_tied_ranks(self):
        """Test with tied ranks (common in real data)."""
        x = np.array([1, 2, 2, 2, 5])
        y = np.array([2, 4, 4, 4, 10])

        rho, p_value = calculate_spearman_correlation(x, y)

        # Should handle ties correctly and remain in bounds
        assert -1.0 <= rho <= 1.0, f"Tied ranks rho {rho} out of bounds"
        assert 0.0 <= p_value <= 1.0, f"Tied ranks p-value {p_value} out of bounds"

    def test_very_small_p_value(self):
        """Test that very small p-values are handled correctly."""
        x = np.arange(1, 1001)
        y = np.arange(1, 1001) * 2

        rho, p_value = calculate_spearman_correlation(x, y)

        assert rho == 1.0, f"Expected rho=1.0, got {rho}"
        assert p_value == 0.0, f"Expected p=0.0, got {p_value}"

    def test_very_large_p_value(self):
        """Test that large p-values (near 1) are handled correctly."""
        np.random.seed(789)
        x = np.random.randn(100)
        y = np.random.randn(100)

        rho, p_value = calculate_spearman_correlation(x, y)

        assert -1.0 <= rho <= 1.0, f"Large p-value case rho {rho} out of bounds"
        assert 0.0 <= p_value <= 1.0, f"Large p-value case {p_value} out of bounds"

    def test_return_type_consistency(self):
        """Test that function always returns tuple of (float, float)."""
        x = np.random.randn(50)
        y = np.random.randn(50)

        result = calculate_spearman_correlation(x, y)

        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 2, f"Expected 2 values, got {len(result)}"
        assert isinstance(result[0], (float, np.floating)), f"rho should be float, got {type(result[0])}"
        assert isinstance(result[1], (float, np.floating)), f"p-value should be float, got {type(result[1])}"

    def test_deterministic_results(self):
        """Test that same input produces same output (deterministic)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])

        rho1, p1 = calculate_spearman_correlation(x, y)
        rho2, p2 = calculate_spearman_correlation(x, y)

        assert rho1 == rho2, f"Non-deterministic: {rho1} != {rho2}"
        assert p1 == p2, f"Non-deterministic: {p1} != {p2}"

    def test_symmetry(self):
        """Test that correlation(x, y) == correlation(y, x)."""
        x = np.random.randn(100)
        y = np.random.randn(100)

        rho_xy, p_xy = calculate_spearman_correlation(x, y)
        rho_yx, p_yx = calculate_spearman_correlation(y, x)

        assert rho_xy == rho_yx, f"Non-symmetric: rho_xy={rho_xy} != rho_yx={rho_yx}"
        assert p_xy == p_yx, f"Non-symmetric: p_xy={p_xy} != p_yx={p_yx}"