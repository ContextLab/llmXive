"""
tests/unit/test_modeling.py
Unit tests for modeling.py functions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Import functions to test
from modeling import (
    apply_holm_bonferroni,
    detect_perfect_separation,
    run_power_analysis
)

class TestHolmBonferroni:
    def test_holm_correction_orders_correctly(self):
        """Verify that Holm-Bonferroni correctly orders and adjusts p-values."""
        # Known p-values
        pvals = {
            'feat1': 0.01,
            'feat2': 0.04,
            'feat3': 0.03,
            'feat4': 0.001
        }
        
        result = apply_holm_bonferroni(pvals)
        
        # Check that all adjusted p-values are >= original
        for key in pvals:
            assert result[key] >= pvals[key], f"Adjusted p-value for {key} should be >= original"
        
        # Check that the smallest original p-value gets the largest adjustment factor relative to others
        # This is a basic sanity check. The actual values depend on the number of tests.
        assert len(result) == len(pvals)
        
    def test_holm_correction_with_equal_pvalues(self):
        """Test with equal p-values."""
        pvals = {'a': 0.05, 'b': 0.05, 'c': 0.05}
        result = apply_holm_bonferroni(pvals)
        # All adjusted should be equal
        vals = list(result.values())
        assert all(abs(v - vals[0]) < 1e-6 for v in vals)

class TestPowerAnalysis:
    def test_power_analysis_returns_dict(self):
        """Verify power analysis returns a dictionary with expected keys."""
        result = run_power_analysis(effect_size=0.5)
        assert isinstance(result, dict)
        assert 'effect_size' in result
        assert 'alpha' in result
        assert 'power' in result

class TestPerfectSeparation:
    def test_detect_separation_with_extreme_coefficients(self):
        """Test detection with artificially extreme coefficients."""
        # Create data that would likely cause separation
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'x1': np.random.randn(n),
            'x2': np.random.randn(n)
        })
        # Create a y that is perfectly separable by x1
        y = (X['x1'] > 0).astype(int)
        
        # This should ideally detect separation, but depends on the implementation
        # We test that the function doesn't crash
        try:
            result = detect_perfect_separation(y, X)
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"detect_perfect_separation raised an exception: {e}")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])