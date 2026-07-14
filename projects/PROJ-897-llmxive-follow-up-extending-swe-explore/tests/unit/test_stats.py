"""
Unit tests for the Wilcoxon signed-rank test implementation in code/analysis/stats.py.

This module verifies:
1. Correct calculation of the Wilcoxon statistic (W) and p-value.
2. Proper handling of ties (continuity correction).
3. Correct handling of zero differences (exclusion).
4. Two-sided vs one-sided test logic.
5. Integration with Bonferroni correction logic (if applicable).

These tests do NOT require external data; they use synthetic but deterministic
datasets to verify statistical correctness against known values or scipy.stats.
"""
import pytest
import numpy as np
from scipy import stats as scipy_stats
import sys
from pathlib import Path

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.stats import wilcoxon_signed_rank, bonferroni_correct


class TestWilcoxonSignedRank:
    """Tests for the wilcoxon_signed_rank function."""

    def test_perfect_match_all_zeros(self):
        """
        Test case where all differences are zero.
        Expected: W=0, p-value=1.0 (or handled gracefully).
        """
        x = [1.0, 2.0, 3.0]
        y = [1.0, 2.0, 3.0]
        # Our implementation should handle this.
        # If we exclude zeros, we have 0 samples -> W=0, p=1.0 by convention or raise.
        # We expect a result that is mathematically consistent.
        w, p = wilcoxon_signed_rank(x, y)
        # With no non-zero differences, scipy returns W=0.0, p=1.0
        assert p == 1.0
        assert w == 0.0

    def test_simple_alternating_signs(self):
        """
        Test with a known small dataset.
        x = [1, 2, 3, 4]
        y = [2, 1, 4, 3]
        Diffs = [-1, 1, -1, 1] -> Ranks = [1.5, 1.5, 1.5, 1.5] (ties)
        W+ = 1.5 + 1.5 = 3.0
        W- = 1.5 + 1.5 = 3.0
        W = min(3, 3) = 3.0
        """
        x = [1.0, 2.0, 3.0, 4.0]
        y = [2.0, 1.0, 4.0, 3.0]
        w, p = wilcoxon_signed_rank(x, y)
        
        # Compare against scipy
        scipy_w, scipy_p = scipy_stats.wilcoxon(x, y, zero_method='wilcox', correction=False)
        
        # Allow small floating point differences
        assert abs(w - scipy_w) < 1e-6
        assert abs(p - scipy_p) < 1e-6

    def test_with_ties_and_continuity_correction(self):
        """
        Test that continuity correction is applied when ties exist.
        """
        x = [10, 20, 30, 40, 50]
        y = [12, 22, 30, 42, 52] # Diffs: -2, -2, 0, -2, -2
        # Non-zero diffs: -2, -2, -2, -2. Ranks: 1, 2, 3, 4. Sum = 10. W=10.
        # Ties in diffs (-2 appears 4 times).
        w, p = wilcoxon_signed_rank(x, y)
        
        # Scipy with correction=True (default)
        scipy_w, scipy_p = scipy_stats.wilcoxon(x, y, zero_method='wilcox', correction=True)
        
        assert abs(w - scipy_w) < 1e-6
        # p-values might differ slightly due to exact vs approximation, but should be close
        assert abs(p - scipy_p) < 1e-4

    def test_one_sided_greater(self):
        """
        Test one-sided test (alternative='greater').
        """
        x = [1, 2, 3, 4, 5]
        y = [0, 1, 2, 3, 4] # x > y mostly
        
        # Two-sided first
        w_two, p_two = wilcoxon_signed_rank(x, y, alternative='two-sided')
        # One-sided greater
        w_one, p_one = wilcoxon_signed_rank(x, y, alternative='greater')
        
        # For one-sided, p should be roughly half of two-sided if direction matches
        # Note: scipy behavior for one-sided is p/2 if direction is correct
        scipy_w, scipy_p = scipy_stats.wilcoxon(x, y, alternative='greater')
        
        assert abs(w_one - scipy_w) < 1e-6
        assert abs(p_one - scipy_p) < 1e-4

    def test_different_sample_sizes(self):
        """
        Test that the function raises an error for mismatched lengths.
        """
        x = [1, 2, 3]
        y = [1, 2]
        
        with pytest.raises(ValueError):
            wilcoxon_signed_rank(x, y)

    def test_empty_input(self):
        """
        Test behavior with empty lists.
        """
        x = []
        y = []
        
        # Should handle gracefully, likely returning W=0, p=1.0
        w, p = wilcoxon_signed_rank(x, y)
        assert w == 0.0
        assert p == 1.0


class TestBonferroniCorrection:
    """Tests for the bonferroni_correct function."""

    def test_single_test(self):
        """
        With 1 test, corrected p should equal original p.
        """
        p_val = 0.05
        corrected = bonferroni_correct([p_val], alpha=0.05)
        assert corrected == p_val

    def test_multiple_tests_simple(self):
        """
        With 2 tests, corrected p should be p * 2.
        """
        p_vals = [0.02, 0.03]
        corrected = bonferroni_correct(p_vals, alpha=0.05)
        expected = [0.04, 0.06]
        assert corrected == expected

    def test_cap_at_1(self):
        """
        Corrected p-values should not exceed 1.0.
        """
        p_vals = [0.6, 0.7]
        corrected = bonferroni_correct(p_vals, alpha=0.05)
        # 0.6 * 2 = 1.2 -> capped at 1.0
        # 0.7 * 2 = 1.4 -> capped at 1.0
        assert corrected[0] == 1.0
        assert corrected[1] == 1.0

    def test_significance_threshold(self):
        """
        Test that the function correctly identifies significant results.
        """
        p_vals = [0.01, 0.03, 0.1]
        corrected = bonferroni_correct(p_vals, alpha=0.05)
        
        # 0.01 * 3 = 0.03 (sig)
        # 0.03 * 3 = 0.09 (not sig)
        # 0.1 * 3 = 0.3 (not sig)
        assert corrected[0] < 0.05
        assert corrected[1] >= 0.05
        assert corrected[2] >= 0.05

    def test_alpha_parameter(self):
        """
        Test with a different alpha value.
        """
        p_vals = [0.01, 0.02]
        # Alpha = 0.1, n=2 -> threshold = 0.05
        corrected = bonferroni_correct(p_vals, alpha=0.1)
        # 0.01 * 2 = 0.02 (< 0.1, sig)
        # 0.02 * 2 = 0.04 (< 0.1, sig)
        assert corrected[0] < 0.1
        assert corrected[1] < 0.1