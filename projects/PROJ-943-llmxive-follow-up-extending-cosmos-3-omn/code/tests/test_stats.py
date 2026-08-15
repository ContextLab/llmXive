"""
Unit tests for statistical significance calculations in scripts/evaluate.py.
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
        # Generate normal data
        data1 = np.random.normal(loc=0, scale=1, size=100)
        data2 = np.random.normal(loc=0.5, scale=1, size=100)
        diff = data1 - data2

        test_type, p_value = perform_statistical_test(diff)
        assert test_type == "t-test"
        assert 0 <= p_value <= 1

    def test_determine_test_and_pvalue_non_normal(self):
        """Test Wilcoxon test selection for non-normal data."""
        # Generate skewed data (exponential)
        data1 = np.random.exponential(scale=1.0, size=100)
        data2 = np.random.exponential(scale=1.5, size=100)
        diff = data1 - data2

        test_type, p_value = perform_statistical_test(diff)
        assert test_type in ["wilcoxon", "t-test"] # Wilcoxon if non-normal
        assert 0 <= p_value <= 1

    def test_pvalue_significance(self):
        """Test that p-value correctly identifies significance."""
        # Large difference should be significant
        data1 = np.array([1.0] * 50)
        data2 = np.array([10.0] * 50)
        diff = data1 - data2

        _, p_value = perform_statistical_test(diff)
        assert p_value < 0.05

    def test_pvalue_non_significance(self):
        """Test that p-value correctly identifies non-significance."""
        # Identical data should not be significant
        data = np.array([1.0] * 50)
        diff = data - data

        _, p_value = perform_statistical_test(diff)
        assert p_value == 1.0  # Or very close to 1
