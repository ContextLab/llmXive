"""
Unit tests for Bonferroni correction logic.

This module tests the `bonferroni_correct` function which adjusts p-values
to account for multiple hypothesis testing.
"""

import pytest
import numpy as np
from code.utils import bonferroni_correct


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction utility function."""

    def test_single_pvalue(self):
        """Test correction with a single p-value."""
        p_values = [0.05]
        adjusted = bonferroni_correct(p_values)
        # With m=1, adjusted should equal original
        assert np.isclose(adjusted[0], 0.05)

    def test_multiple_pvalues(self):
        """Test correction with multiple p-values."""
        p_values = [0.01, 0.05, 0.10]
        adjusted = bonferroni_correct(p_values)
        m = len(p_values)
        expected = [p * m for p in p_values]
        for a, e in zip(adjusted, expected):
            assert np.isclose(a, e)

    def test_cap_at_one(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.9]
        m = len(p_values)
        # 0.9 * 3 = 2.7, should be capped to 1.0
        adjusted = bonferroni_correct(p_values)
        assert all(p <= 1.0 for p in adjusted)
        assert np.isclose(adjusted[-1], 1.0)

    def test_empty_list(self):
        """Test behavior with an empty list of p-values."""
        p_values = []
        adjusted = bonferroni_correct(p_values)
        assert adjusted == []

    def test_numpy_array_input(self):
        """Test that numpy arrays are handled correctly."""
        p_values = np.array([0.02, 0.04, 0.06])
        adjusted = bonferroni_correct(p_values)
        assert isinstance(adjusted, list)
        assert len(adjusted) == len(p_values)

    def test_significance_threshold(self):
        """Test that significant results remain significant after correction."""
        # Original p=0.01 with m=5 -> 0.05, still significant at 0.05
        p_values = [0.01]
        adjusted = bonferroni_correct(p_values)
        assert adjusted[0] <= 0.05

    def test_non_significance_after_correction(self):
        """Test that non-significant results may become non-significant."""
        # Original p=0.02 with m=10 -> 0.2, non-significant at 0.05
        p_values = [0.02]
        adjusted = bonferroni_correct(p_values)
        assert adjusted[0] > 0.05