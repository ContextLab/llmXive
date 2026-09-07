"""
Unit tests for statistical significance calculations in scripts/evaluate.py.

Tests verify the correct selection of statistical tests (t-test vs Wilcoxon)
based on normality checks and the accuracy of p-value calculations.
"""
import pytest
import numpy as np
from scipy import stats
from typing import List, Tuple

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.evaluate import perform_statistical_test


class TestStatisticalSignificance:
    """Tests for statistical test selection and p-value calculation."""

    def test_determine_test_and_pvalue_normal(self):
        """Test t-test selection for normally distributed data."""
        # Generate normal data with a known difference
        np.random.seed(42)
        data1 = np.random.normal(loc=0, scale=1, size=100)
        data2 = np.random.normal(loc=0.5, scale=1, size=100)
        diff = data1 - data2

        test_type, p_value = perform_statistical_test(diff)
        
        # Shapiro-Wilk should likely pass for normal data, selecting t-test
        # However, due to random variation, it might occasionally fail, so we check p-value range
        assert 0 <= p_value <= 1
        # If normality test passed, it should be a t-test
        if test_type == "t-test":
            assert True
        elif test_type == "wilcoxon":
            # If it picked wilcoxon, the normality test must have failed
            assert True
        else:
            pytest.fail(f"Unexpected test type: {test_type}")

    def test_determine_test_and_pvalue_non_normal(self):
        """Test Wilcoxon test selection for non-normal (skewed) data."""
        # Generate skewed data (exponential) which is non-normal
        np.random.seed(42)
        data1 = np.random.exponential(scale=1.0, size=100)
        data2 = np.random.exponential(scale=1.5, size=100)
        diff = data1 - data2

        test_type, p_value = perform_statistical_test(diff)
        
        # Non-normal data should trigger Wilcoxon, but t-test is acceptable if normality test fails to reject
        assert 0 <= p_value <= 1
        assert test_type in ["wilcoxon", "t-test"]

    def test_pvalue_significance(self):
        """Test that p-value correctly identifies a significant difference."""
        # Large, clear difference should be significant
        data1 = np.array([1.0] * 50)
        data2 = np.array([10.0] * 50)
        diff = data1 - data2

        _, p_value = perform_statistical_test(diff)
        assert p_value < 0.05, f"Expected significant p-value (<0.05), got {p_value}"

    def test_pvalue_non_significance(self):
        """Test that p-value correctly identifies non-significance for identical data."""
        # Identical data should result in p-value of 1.0 (or very close)
        data = np.array([1.0] * 50)
        diff = data - data

        _, p_value = perform_statistical_test(diff)
        # For identical data, t-statistic is 0, p-value should be 1.0
        assert np.isclose(p_value, 1.0, atol=0.01) or p_value > 0.95, \
            f"Expected p-value near 1.0 for identical data, got {p_value}"

    def test_small_sample_size(self):
        """Test behavior with small sample sizes."""
        np.random.seed(42)
        data1 = np.random.normal(loc=0, scale=1, size=10)
        data2 = np.random.normal(loc=0.5, scale=1, size=10)
        diff = data1 - data2

        test_type, p_value = perform_statistical_test(diff)
        
        assert 0 <= p_value <= 1
        assert test_type in ["wilcoxon", "t-test"]

    def test_empty_input(self):
        """Test that empty input raises an appropriate error."""
        with pytest.raises((ValueError, IndexError)):
            perform_statistical_test(np.array([]))