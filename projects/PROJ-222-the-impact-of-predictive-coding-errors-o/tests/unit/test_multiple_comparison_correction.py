import pytest
import numpy as np
from statsmodels.stats.multitest import multipletests
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis import run_multiple_comparison_correction

class TestMultipleComparisonCorrection:
    """Tests for T023: Multiple-comparison correction logic."""

    def test_no_correction_single_test(self):
        """Verify that correction is skipped if num_tests == 1."""
        p_values = [0.03]
        result = run_multiple_comparison_correction(p_values)
        assert result == p_values
        assert len(result) == 1

    def test_no_correction_empty_list(self):
        """Verify behavior with empty list."""
        p_values = []
        result = run_multiple_comparison_correction(p_values)
        assert result == []

    def test_bonferroni_correction(self):
        """Verify Bonferroni correction logic."""
        p_values = [0.01, 0.04, 0.5]
        # Expected: 0.01*3=0.03, 0.04*3=0.12, 0.5*3=1.0 (capped at 1)
        expected = [0.03, 0.12, 1.0]
        result = run_multiple_comparison_correction(p_values, method='bonferroni')
        
        for r, e in zip(result, expected):
            assert np.isclose(r, e, atol=1e-6), f"Expected {e}, got {r}"

    def test_fdr_bh_correction(self):
        """Verify Benjamini-Hochberg correction logic."""
        p_values = [0.01, 0.04, 0.5]
        # We trust statsmodels implementation, just check it returns valid probabilities
        result = run_multiple_comparison_correction(p_values, method='fdr_bh')
        
        assert len(result) == 3
        assert all(0 <= p <= 1 for p in result)
        # FDR should generally be less than or equal to Bonferroni (more powerful)
        bonf_result = run_multiple_comparison_correction(p_values, method='bonferroni')
        for fdr_p, bonf_p in zip(result, bonf_result):
            assert fdr_p <= bonf_p, "FDR corrected p-value should be <= Bonferroni"

    def test_correction_applied_when_num_tests_gt_1(self):
        """Verify correction is actually applied when num_tests > 1."""
        p_values = [0.01, 0.02]
        result = run_multiple_comparison_correction(p_values)
        
        # Since correction increases p-values (usually), result should differ from input
        # unless p-values are already 1.0 or 0.0 in specific edge cases.
        # Here 0.01 and 0.02 will definitely change.
        assert result != p_values, "Correction should have been applied."