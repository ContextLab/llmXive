import pytest
import pandas as pd
import numpy as np
from code.analyser import apply_bonferroni_correction, apply_bonferroni_correction_dataframe

class TestBonferroniCorrection:
    def test_basic_correction(self):
        """Test basic Bonferroni correction."""
        p_values = [0.01, 0.05, 0.1]
        adjusted = apply_bonferroni_correction(p_values)
        
        # With 3 tests, each p-value should be multiplied by 3
        expected = [0.03, 0.15, 0.3]
        assert adjusted == expected
    
    def test_correction_caps_at_one(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.7]
        adjusted = apply_bonferroni_correction(p_values)
        
        # 0.5 * 3 = 1.5, should be capped at 1.0
        assert adjusted[0] == 1.0
        assert adjusted[1] == 1.0
        assert adjusted[2] == 1.0
    
    def test_empty_list(self):
        """Test handling of empty list."""
        adjusted = apply_bonferroni_correction([])
        assert adjusted == []
    
    def test_single_p_value(self):
        """Test with a single p-value."""
        p_values = [0.05]
        adjusted = apply_bonferroni_correction(p_values)
        assert adjusted == [0.05]  # 0.05 * 1 = 0.05
    
    def test_dataframe_correction(self):
        """Test Bonferroni correction on DataFrame."""
        df = pd.DataFrame({
            'p_value': [0.01, 0.05, 0.1, 0.2]
        })
        
        result = apply_bonferroni_correction_dataframe(df, 'p_value')
        
        # Check that adjusted column exists
        assert 'p_value_adj' in result.columns
        
        # Check values: 4 tests, so multiply by 4
        expected_adj = [0.04, 0.2, 0.4, 0.8]
        assert list(result['p_value_adj']) == expected_adj
    
    def test_dataframe_with_nan(self):
        """Test handling of NaN values in DataFrame."""
        df = pd.DataFrame({
            'p_value': [0.01, np.nan, 0.05, 0.1]
        })
        
        result = apply_bonferroni_correction_dataframe(df, 'p_value')
        
        # NaN should be handled (filled with 1.0 in the implementation)
        assert pd.isna(result.loc[1, 'p_value'])
        # The adjusted value for NaN should be 1.0 (filled)
        assert result.loc[1, 'p_value_adj'] == 1.0
    
    def test_monotonicity(self):
        """Test that adjusted p-values maintain monotonicity with raw p-values."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        adjusted = apply_bonferroni_correction(p_values)
        
        # Adjusted values should also be monotonically increasing
        for i in range(len(adjusted) - 1):
            assert adjusted[i] <= adjusted[i + 1]
    
    def test_family_wise_error_rate_control(self):
        """
        Test that Bonferroni correction controls FWER.
        
        If we have n independent tests at level alpha, the probability of
        at least one false positive is <= n * alpha (without correction).
        With Bonferroni, we use alpha/n for each test, so the FWER is <= alpha.
        
        This test verifies the mathematical property of the correction.
        """
        # Simulate a case where we have many small p-values
        p_values = [0.001] * 10  # 10 tests, all with p=0.001
        adjusted = apply_bonferroni_correction(p_values)
        
        # Each should be 0.001 * 10 = 0.01
        assert all(abs(adj - 0.01) < 1e-10 for adj in adjusted)
    
    def test_large_family(self):
        """Test with a large number of tests."""
        n_tests = 100
        p_values = [0.05 / n_tests] * n_tests  # All at the Bonferroni threshold
        adjusted = apply_bonferroni_correction(p_values)
        
        # Each should be exactly 0.05
        assert all(abs(adj - 0.05) < 1e-10 for adj in adjusted)
    
    def test_mixed_p_values(self):
        """Test with a mix of very small and large p-values."""
        p_values = [1e-10, 0.001, 0.05, 0.5, 0.9]
        adjusted = apply_bonferroni_correction(p_values)
        
        # n = 5
        expected = [5e-10, 0.005, 0.25, 1.0, 1.0]
        assert adjusted == expected