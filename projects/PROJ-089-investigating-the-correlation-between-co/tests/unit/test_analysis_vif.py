"""
Unit tests for VIF calculation and Ridge regression fallback in analysis.py.
"""

import pytest
import pandas as pd
import numpy as np
from code.analysis import check_vif, fit_mixed_effects_model


class TestVIFCheck:
    """Tests for the VIF calculation function."""
    
    def test_no_collinearity(self):
        """Test VIF with uncorrelated variables."""
        np.random.seed(42)
        df = pd.DataFrame({
            'x1': np.random.randn(100),
            'x2': np.random.randn(100),
            'x3': np.random.randn(100)
        })
        
        high_vif, vif_values = check_vif(df, ['x1', 'x2', 'x3'])
        
        assert not high_vif, "Should not detect high collinearity in random data"
        for col, vif in vif_values.items():
            assert vif < 5.0, f"VIF for {col} should be < 5, got {vif}"
            
    def test_high_collinearity(self):
        """Test VIF with highly correlated variables."""
        np.random.seed(42)
        base = np.random.randn(100)
        df = pd.DataFrame({
            'x1': base,
            'x2': base * 0.95 + np.random.randn(100) * 0.1,  # Highly correlated
            'x3': np.random.randn(100)
        })
        
        high_vif, vif_values = check_vif(df, ['x1', 'x2', 'x3'])
        
        assert high_vif, "Should detect high collinearity"
        assert vif_values['x1'] > 5.0 or vif_values['x2'] > 5.0, "At least one VIF should exceed threshold"
        
    def test_missing_columns(self):
        """Test VIF with missing columns."""
        df = pd.DataFrame({'x1': [1, 2, 3]})
        
        high_vif, vif_values = check_vif(df, ['x1', 'x2'])
        
        assert not high_vif
        assert 'x1' in vif_values
        assert 'x2' not in vif_values
        
    def test_empty_dataframe(self):
        """Test VIF with empty DataFrame."""
        df = pd.DataFrame()
        
        high_vif, vif_values = check_vif(df, ['x1'])
        
        assert not high_vif
        assert vif_values == {}
        
    def test_single_column(self):
        """Test VIF with a single column."""
        df = pd.DataFrame({'x1': [1, 2, 3, 4, 5]})
        
        high_vif, vif_values = check_vif(df, ['x1'])
        
        # VIF for single predictor (with intercept) should be 1.0
        assert not high_vif
        assert abs(vif_values['x1'] - 1.0) < 0.1


class TestMixedEffectsWithRidge:
    """Tests for mixed-effects model with Ridge fallback."""
    
    def test_ridge_applied_on_high_vif(self):
        """Test that Ridge is applied when VIF is high."""
        np.random.seed(42)
        n = 200
        base = np.random.randn(n)
        
        df = pd.DataFrame({
            'y': base + np.random.randn(n) * 0.5,
            'x1': base,
            'x2': base * 0.9 + np.random.randn(n) * 0.1,
            'repo_id': ['repo1'] * (n // 2) + ['repo2'] * (n // 2)
        })
        
        # Should not raise, should apply Ridge
        results = fit_mixed_effects_model(
            df,
            target='y',
            fixed_effects=['x1', 'x2'],
            group_col='repo_id',
            use_ridge=True
        )
        
        assert results['use_ridge'] is True
        assert 'ridge_coefs' in results
        assert 'ridge_score' in results
        
    def test_standard_model_on_low_vif(self):
        """Test standard mixed-effects model on low collinearity data."""
        np.random.seed(42)
        n = 200
        
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.random.randn(n),
            'repo_id': ['repo1'] * (n // 2) + ['repo2'] * (n // 2)
        })
        
        results = fit_mixed_effects_model(
            df,
            target='y',
            fixed_effects=['x1', 'x2'],
            group_col='repo_id',
            use_ridge=False
        )
        
        assert results['use_ridge'] is False
        assert 'fixed_effects_coef' in results
        
    def test_insufficient_data(self):
        """Test error handling for insufficient data."""
        df = pd.DataFrame({
            'y': [1, 2],
            'x1': [1, 2],
            'repo_id': ['a', 'b']
        })
        
        with pytest.raises(ValueError):
            fit_mixed_effects_model(
                df,
                target='y',
                fixed_effects=['x1'],
                group_col='repo_id'
            )

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
