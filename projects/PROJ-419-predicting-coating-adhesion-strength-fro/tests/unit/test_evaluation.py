"""
Unit tests for Bonferroni correction logic in code/evaluation.py.

This test module verifies the correctness of the Bonferroni correction implementation,
ensuring that p-values are adjusted correctly for multiple hypothesis testing.
"""

import pytest
import numpy as np
from code.evaluation import apply_bonferroni_correction


class TestBonferroniCorrection:
    """Test suite for Bonferroni correction logic."""

    def test_single_pvalue_no_adjustment(self):
        """Test that a single p-value is multiplied by 1 (no change)."""
        p_values = [0.05]
        adjusted = apply_bonferroni_correction(p_values)
        assert len(adjusted) == 1
        assert np.isclose(adjusted[0], 0.05)

    def test_multiple_pvalues_basic(self):
        """Test basic Bonferroni correction with known values."""
        p_values = [0.01, 0.02, 0.03]
        # Bonferroni: p_adj = p * m, capped at 1.0
        # m = 3
        # 0.01 * 3 = 0.03
        # 0.02 * 3 = 0.06
        # 0.03 * 3 = 0.09
        expected = [0.03, 0.06, 0.09]
        adjusted = apply_bonferroni_correction(p_values)
        assert len(adjusted) == len(p_values)
        for a, e in zip(adjusted, expected):
            assert np.isclose(a, e)

    def test_pvalue_capped_at_one(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.7]
        # m = 3
        # 0.5 * 3 = 1.5 -> 1.0
        # 0.6 * 3 = 1.8 -> 1.0
        # 0.7 * 3 = 2.1 -> 1.0
        expected = [1.0, 1.0, 1.0]
        adjusted = apply_bonferroni_correction(p_values)
        for a in adjusted:
            assert a == 1.0

    def test_empty_list(self):
        """Test behavior with an empty list of p-values."""
        p_values = []
        adjusted = apply_bonferroni_correction(p_values)
        assert adjusted == []

    def test_significance_threshold_application(self):
        """Test that corrected p-values correctly affect significance decisions."""
        p_values = [0.01, 0.02, 0.04, 0.06]
        alpha = 0.05
        adjusted = apply_bonferroni_correction(p_values)
        # m = 4
        # 0.01 * 4 = 0.04 (sig)
        # 0.02 * 4 = 0.08 (not sig)
        # 0.04 * 4 = 0.16 (not sig)
        # 0.06 * 4 = 0.24 (not sig)
        significant = [p < alpha for p in adjusted]
        expected_significant = [True, False, False, False]
        assert significant == expected_significant

    def test_numerical_precision(self):
        """Test numerical precision with very small p-values."""
        p_values = [1e-10, 1e-5, 0.001]
        m = 3
        adjusted = apply_bonferroni_correction(p_values)
        assert np.isclose(adjusted[0], 3e-10)
        assert np.isclose(adjusted[1], 3e-5)
        assert np.isclose(adjusted[2], 0.003)

    def test_unsorted_input(self):
        """Test that input order is preserved regardless of sorting."""
        p_values = [0.05, 0.01, 0.03]
        adjusted = apply_bonferroni_correction(p_values)
        # Order must match input order
        assert np.isclose(adjusted[0], 0.15)
        assert np.isclose(adjusted[1], 0.03)
        assert np.isclose(adjusted[2], 0.09)

    def test_large_number_of_tests(self):
        """Test with a large number of comparisons to ensure stability."""
        n_tests = 1000
        p_values = [0.05] * n_tests
        adjusted = apply_bonferroni_correction(p_values)
        # All should be 0.05 * 1000 = 50 -> capped at 1.0
        for val in adjusted:
            assert val == 1.0

    def test_mixed_significance(self):
        """Test a mix of significant and non-significant results after correction."""
        p_values = [0.001, 0.01, 0.02, 0.05, 0.1]
        # m = 5
        # 0.001 * 5 = 0.005 (sig)
        # 0.01 * 5 = 0.05 (sig, exactly at alpha)
        # 0.02 * 5 = 0.10 (not sig)
        # 0.05 * 5 = 0.25 (not sig)
        # 0.1 * 5 = 0.50 (not sig)
        adjusted = apply_bonferroni_correction(p_values)
        alpha = 0.05
        results = [p <= alpha for p in adjusted]
        expected = [True, True, False, False, False]
        assert results == expected