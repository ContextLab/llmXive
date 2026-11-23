import pytest
import numpy as np
import pandas as pd
from src.analysis.stats import bonferroni_correction

class TestBonferroniCorrection:
    """Unit tests for Bonferroni correction logic in src/analysis/stats.py"""

    def test_bonferroni_single_comparison(self):
        """Test with a single p-value (no correction needed effectively)"""
        p_values = [0.05]
        corrected = bonferroni_correction(p_values)
        assert len(corrected) == 1
        # With 1 comparison, corrected p should be min(0.05 * 1, 1.0)
        assert corrected[0] == pytest.approx(0.05)

    def test_bonferroni_multiple_comparisons(self):
        """Test standard Bonferroni correction with multiple p-values"""
        p_values = [0.01, 0.02, 0.05, 0.10]
        corrected = bonferroni_correction(p_values)
        
        # m = 4 comparisons
        # Expected: [0.01*4, 0.02*4, 0.05*4, 0.10*4] capped at 1.0
        expected = [0.04, 0.08, 0.20, 1.0]
        
        assert len(corrected) == len(p_values)
        for c, e in zip(corrected, expected):
            assert c == pytest.approx(e)

    def test_bonferroni_capping_at_one(self):
        """Test that corrected p-values are capped at 1.0"""
        p_values = [0.5, 0.6, 0.9]
        corrected = bonferroni_correction(p_values)
        
        # m = 3
        # 0.5*3=1.5 -> 1.0, 0.6*3=1.8 -> 1.0, 0.9*3=2.7 -> 1.0
        expected = [1.0, 1.0, 1.0]
        
        assert corrected == expected

    def test_bonferroni_empty_list(self):
        """Test behavior with empty list of p-values"""
        p_values = []
        corrected = bonferroni_correction(p_values)
        assert corrected == []

    def test_bonferroni_preserves_order(self):
        """Test that the order of p-values is preserved after correction"""
        p_values = [0.10, 0.01, 0.05, 0.02]
        corrected = bonferroni_correction(p_values)
        
        # Order should be preserved, only values change
        assert len(corrected) == len(p_values)
        # Check that the smallest original p-value results in the smallest corrected p-value
        # Original index 1 (0.01) should map to smallest corrected value
        assert corrected[1] < corrected[0]
        assert corrected[1] < corrected[2]
        assert corrected[1] < corrected[3]

    def test_bonferroni_numpy_array_input(self):
        """Test with numpy array input"""
        p_values = np.array([0.01, 0.02, 0.03])
        corrected = bonferroni_correction(p_values)
        
        assert len(corrected) == 3
        expected = [0.03, 0.06, 0.09]
        for c, e in zip(corrected, expected):
            assert c == pytest.approx(e)

    def test_bonferroni_pandas_series_input(self):
        """Test with pandas Series input"""
        p_values = pd.Series([0.05, 0.10, 0.15])
        corrected = bonferroni_correction(p_values)
        
        assert len(corrected) == 3
        expected = [0.15, 0.30, 0.45]
        for c, e in zip(corrected, expected):
            assert c == pytest.approx(e)

    def test_bonferroni_significance_threshold(self):
        """Test that corrected p-values correctly determine significance at alpha=0.05"""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected = bonferroni_correction(p_values)
        
        # m = 5, alpha = 0.05
        # Threshold for original p: 0.05/5 = 0.01
        # Only p=0.01 should remain significant (corrected = 0.05)
        
        # p=0.01 -> corrected=0.05 (significant at alpha=0.05)
        assert corrected[0] <= 0.05
        # p=0.02 -> corrected=0.10 (not significant)
        assert corrected[1] > 0.05
        # p=0.03 -> corrected=0.15 (not significant)
        assert corrected[2] > 0.05

    def test_bonferroni_edge_case_very_small_p(self):
        """Test with very small p-values"""
        p_values = [1e-10, 1e-8, 1e-6]
        corrected = bonferroni_correction(p_values)
        
        m = 3
        expected = [3e-10, 3e-8, 3e-6]
        for c, e in zip(corrected, expected):
            assert c == pytest.approx(e)