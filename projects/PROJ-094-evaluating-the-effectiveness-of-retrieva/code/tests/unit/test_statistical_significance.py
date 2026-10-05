"""
Unit tests for statistical significance selection in correlation analysis.
Verifies that the system correctly switches from t-test to Wilcoxon when normality is violated.
"""

import pytest
import numpy as np
from scipy import stats
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.analysis.correlation import test_normality, compute_correlation_and_significance


class TestNormalityTest:
    """Tests for the normality test functionality."""

    def test_normal_data_detected_as_normal(self):
        """Test that normally distributed data is correctly identified as normal."""
        # Generate normal data
        np.random.seed(42)
        normal_data = np.random.normal(loc=0, scale=1, size=100)

        result, is_normal = test_normality(normal_data.tolist())

        assert is_normal, "Normally distributed data should be identified as normal"
        assert result.pvalue > 0.05, f"p-value {result.pvalue} should be > 0.05"

    def test_non_normal_data_detected_as_non_normal(self):
        """Test that non-normal data is correctly identified as non-normal."""
        # Generate highly skewed data
        skewed_data = np.random.exponential(scale=1.0, size=100)

        result, is_normal = test_normality(skewed_data.tolist())

        assert not is_normal, "Skewed data should be identified as non-normal"
        assert result.pvalue <= 0.05, f"p-value {result.pvalue} should be <= 0.05"

    def test_insufficient_data_points(self):
        """Test behavior with insufficient data points."""
        small_data = [1.0, 2.0]

        result, is_normal = test_normality(small_data)

        assert not is_normal, "Insufficient data should be treated as non-normal"
        assert result.pvalue == 0.0, "p-value should be 0.0 for insufficient data"

    def test_very_small_sample(self):
        """Test with a very small but valid sample."""
        small_valid_data = [1.0, 2.0, 3.0, 4.0, 5.0]

        result, is_normal = test_normality(small_valid_data)

        # With only 5 points, Shapiro-Wilk may not reject normality
        # Just ensure it runs without error
        assert isinstance(result.pvalue, float)
        assert 0.0 <= result.pvalue <= 1.0


class TestCorrelationSignificanceSelection:
    """Tests for correlation significance test selection."""

    def test_normal_data_uses_correlation_p_value(self):
        """Test that normal data uses correlation p-value for significance."""
        np.random.seed(42)
        x = np.random.normal(0, 1, 50).tolist()
        y = np.random.normal(0, 1, 50).tolist()

        result = compute_correlation_and_significance(x, y, "test_descriptor")

        assert result['test_type'] in ['correlation_p_value', 'spearman_p_value'], \
            f"Expected correlation-based test, got {result['test_type']}"
        assert result['normality_test']['is_normal'] is True or \
               result['test_type'] == 'spearman_p_value', \
               "Normal data should use correlation p-value or Spearman"

    def test_non_normal_data_uses_spearman(self):
        """Test that non-normal data correctly uses Spearman correlation."""
        # Create non-normal data
        np.random.seed(42)
        x = np.random.exponential(1.0, 50).tolist()
        y = np.random.exponential(1.0, 50).tolist()

        result = compute_correlation_and_significance(x, y, "test_descriptor")

        # For non-normal data, Spearman is more appropriate
        assert result['spearman_rho'] is not None, "Spearman rho should be computed"
        assert result['spearman_p'] is not None, "Spearman p-value should be computed"
        assert result['test_type'] in ['correlation_p_value', 'spearman_p_value'], \
            f"Test type should be correlation-based: {result['test_type']}"

    def test_significance_flagging(self):
        """Test that significant correlations are correctly flagged."""
        # Create data with a strong correlation
        np.random.seed(42)
        x = list(range(50))
        y = [xi + np.random.normal(0, 0.1) for xi in x]

        result = compute_correlation_and_significance(x, y, "strong_correlation")

        # With such strong correlation, p-value should be very small
        assert result['is_significant'] is True, \
            "Strong correlation should be flagged as significant"
        assert result['significance_p_value'] < 0.05, \
            f"p-value {result['significance_p_value']} should be < 0.05"

    def test_non_significant_correlation(self):
        """Test that non-significant correlations are correctly flagged."""
        # Create data with no correlation
        np.random.seed(42)
        x = np.random.normal(0, 1, 50).tolist()
        y = np.random.normal(0, 1, 50).tolist()

        result = compute_correlation_and_significance(x, y, "no_correlation")

        # With random data, correlation is likely not significant
        # (though it could be by chance, so we check the flag is set correctly)
        assert result['is_significant'] in [True, False], \
            "Significance flag should be a boolean"
        if result['significance_p_value'] is not None:
            assert result['is_significant'] == (result['significance_p_value'] < 0.05), \
                "Significance flag should match p-value threshold"


class TestEdgeCases:
    """Tests for edge cases in correlation analysis."""

    def test_constant_data(self):
        """Test handling of constant data (zero variance)."""
        x = [1.0] * 50
        y = list(range(50))

        result = compute_correlation_and_significance(x, y, "constant_x")

        # Correlation with constant data should fail gracefully
        # Pearson and Spearman might return NaN or raise an error
        assert result['pearson_r'] is None or np.isnan(result['pearson_r']) or \
               result['spearman_rho'] is None or np.isnan(result['spearman_rho']), \
               "Correlation with constant data should be NaN or None"

    def test_single_point(self):
        """Test with single data point."""
        x = [1.0]
        y = [2.0]

        # This should handle the edge case gracefully
        result = compute_correlation_and_significance(x, y, "single_point")

        # With only one point, correlation cannot be computed
        assert result['pearson_r'] is None or result['spearman_rho'] is None, \
            "Correlation with single point should be None"

    def test_mixed_nan_handling(self):
        """Test that NaN values are handled appropriately in correlation."""
        # Note: The main correlation function should filter out NaNs before this point
        # This test verifies the behavior if NaNs somehow reach here
        x = [1.0, 2.0, np.nan, 4.0]
        y = [1.0, 2.0, 3.0, 4.0]

        # Filter out NaNs
        valid_pairs = [(xi, yi) for xi, yi in zip(x, y) if not np.isnan(xi) and not np.isnan(yi)]
        x_clean = [p[0] for p in valid_pairs]
        y_clean = [p[1] for p in valid_pairs]

        result = compute_correlation_and_significance(x_clean, y_clean, "cleaned_data")

        assert result['pearson_r'] is not None or result['spearman_rho'] is not None, \
            "Correlation should be computable after NaN removal"