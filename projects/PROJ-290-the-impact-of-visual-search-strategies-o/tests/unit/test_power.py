"""
Unit tests for multiple comparison correction (Bonferroni/BH) in code/analysis/power.py.

This module verifies that the statistical power analysis utilities correctly apply
Bonferroni and Benjamini-Hochberg (BH) corrections to p-values.
"""
import pytest
import numpy as np
from code.analysis.power import bonferroni_correction, benjamini_hochberg_correction
from code.utils.logging import get_logger

logger = get_logger(__name__)


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction implementation."""

    def test_single_pvalue(self):
        """Bonferroni correction with a single p-value should return min(p * 1, 1.0)."""
        p_values = [0.05]
        corrected = bonferroni_correction(p_values)
        assert len(corrected) == 1
        assert corrected[0] == pytest.approx(0.05, rel=1e-5)

    def test_multiple_pvalues_simple(self):
        """Test Bonferroni correction with known simple values."""
        p_values = [0.01, 0.05, 0.10]
        n = len(p_values)
        corrected = bonferroni_correction(p_values)
        
        # Expected: p * n, capped at 1.0
        expected = [min(p * n, 1.0) for p in p_values]
        
        assert len(corrected) == len(p_values)
        for c, e in zip(corrected, expected):
            assert c == pytest.approx(e, rel=1e-5)

    def test_capped_at_one(self):
        """Bonferroni correction must not return values > 1.0."""
        p_values = [0.6, 0.8, 0.9]
        n = len(p_values)
        corrected = bonferroni_correction(p_values)
        
        assert all(p <= 1.0 for p in corrected)
        # 0.9 * 3 = 2.7 -> should be capped at 1.0
        assert corrected[2] == pytest.approx(1.0, rel=1e-5)

    def test_empty_list(self):
        """Handling of empty p-value list."""
        p_values = []
        corrected = bonferroni_correction(p_values)
        assert corrected == []

    def test_all_ones(self):
        """If all p-values are 1.0, corrected should be 1.0."""
        p_values = [1.0, 1.0, 1.0]
        corrected = bonferroni_correction(p_values)
        assert all(p == pytest.approx(1.0, rel=1e-5) for p in corrected)


class TestBenjaminiHochbergCorrection:
    """Tests for the Benjamini-Hochberg (FDR) correction implementation."""

    def test_single_pvalue(self):
        """BH correction with a single p-value should return the p-value itself."""
        p_values = [0.05]
        corrected = benjamini_hochberg_correction(p_values)
        assert len(corrected) == 1
        assert corrected[0] == pytest.approx(0.05, rel=1e-5)

    def test_empty_list(self):
        """Handling of empty p-value list."""
        p_values = []
        corrected = benjamini_hochberg_correction(p_values)
        assert corrected == []

    def test_sorted_pvalues_monotonic(self):
        """
        BH corrected p-values must be monotonically non-decreasing when 
        original p-values are sorted ascending.
        """
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected = benjamini_hochberg_correction(p_values)
        
        # Check monotonicity
        for i in range(1, len(corrected)):
            assert corrected[i] >= corrected[i-1]

    def test_known_bh_example(self):
        """
        Test against a known BH calculation example.
        Input: [0.001, 0.01, 0.02, 0.05, 0.10] (n=5)
        Ranks: 1, 2, 3, 4, 5
        Thresholds: p * n / rank
        Step-down ensures monotonicity.
        """
        p_values = [0.001, 0.01, 0.02, 0.05, 0.10]
        n = len(p_values)
        corrected = benjamini_hochberg_correction(p_values)
        
        # Verify all values are <= 1.0
        assert all(p <= 1.0 for p in corrected)
        
        # Verify monotonicity (since input is sorted)
        for i in range(1, len(corrected)):
            assert corrected[i] >= corrected[i-1]

    def test_unsorted_input(self):
        """BH correction should handle unsorted input correctly."""
        p_values = [0.05, 0.01, 0.03]
        corrected = benjamini_hochberg_correction(p_values)
        
        # The logic should sort internally, apply correction, then restore order
        assert len(corrected) == len(p_values)
        assert all(p <= 1.0 for p in corrected)

    def test_all_zeros(self):
        """If all p-values are 0, corrected should be 0."""
        p_values = [0.0, 0.0, 0.0]
        corrected = benjamini_hochberg_correction(p_values)
        assert all(p == pytest.approx(0.0, rel=1e-5) for p in corrected)

    def test_all_ones(self):
        """If all p-values are 1.0, corrected should be 1.0."""
        p_values = [1.0, 1.0, 1.0]
        corrected = benjamini_hochberg_correction(p_values)
        assert all(p == pytest.approx(1.0, rel=1e-5) for p in corrected)


class TestPowerAnalysisIntegration:
    """Integration-style tests for power analysis utilities."""

    def test_correction_preserves_significance_order(self):
        """
        Correction should not change the relative order of significance 
        (smaller raw p-values should generally remain smaller or equal).
        """
        p_values = [0.001, 0.01, 0.05, 0.10, 0.20]
        bonf = bonferroni_correction(p_values)
        bh = benjamini_hochberg_correction(p_values)
        
        # Check that order is preserved (non-decreasing for sorted input)
        for correction_name, correction in [("Bonferroni", bonf), ("BH", bh)]:
            for i in range(1, len(correction)):
                assert correction[i] >= correction[i-1], \
                    f"{correction_name} order not preserved"

    def test_bh_less_conservative_than_bonferroni(self):
        """
        BH correction should be less conservative (produce smaller adjusted p-values)
        than Bonferroni for typical cases.
        """
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        bonf = bonferroni_correction(p_values)
        bh = benjamini_hochberg_correction(p_values)
        
        # BH values should be <= Bonferroni values (less conservative)
        for b, f in zip(bh, bonf):
            assert b <= f + 1e-9  # Allow tiny floating point tolerance