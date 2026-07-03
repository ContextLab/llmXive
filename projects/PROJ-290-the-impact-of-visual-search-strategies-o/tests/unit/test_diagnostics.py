"""
Unit tests for VIF (Variance Inflation Factor) calculation in diagnostics.

This test suite verifies the VIF calculation logic used to detect
multicollinearity among predictor variables.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.diagnostics import calculate_vif, calculate_vif_for_pair


class TestVIFCalculation:
    """Tests for VIF calculation functions."""

    def test_calculate_vif_no_collinearity(self):
        """Test VIF calculation with orthogonal predictors (should be ~1.0)."""
        # Create orthogonal data: independent variables
        np.random.seed(42)
        n = 100
        # Generate independent variables
        X = np.random.randn(n, 3)
        df = pd.DataFrame(X, columns=['pred1', 'pred2', 'pred3'])
        
        vif_results = calculate_vif(df)
        
        # VIF should be close to 1.0 for orthogonal predictors
        assert vif_results['pred1']['vif'] < 1.1
        assert vif_results['pred2']['vif'] < 1.1
        assert vif_results['pred3']['vif'] < 1.1

    def test_calculate_vif_high_collinearity(self):
        """Test VIF calculation with highly collinear predictors (should be > 5)."""
        np.random.seed(42)
        n = 100
        
        # Create highly correlated variables
        x1 = np.random.randn(n)
        x2 = x1 + np.random.randn(n) * 0.01  # Nearly identical
        x3 = np.random.randn(n)  # Independent
        
        df = pd.DataFrame({'pred1': x1, 'pred2': x2, 'pred3': x3})
        
        vif_results = calculate_vif(df)
        
        # VIF for collinear variables should be high (> 5)
        assert vif_results['pred1']['vif'] > 5.0
        assert vif_results['pred2']['vif'] > 5.0
        # Independent variable should have low VIF
        assert vif_results['pred3']['vif'] < 2.0

    def test_calculate_vif_perfect_collinearity(self):
        """Test VIF calculation with perfect collinearity (should raise or be very high)."""
        np.random.seed(42)
        n = 100
        
        # Create perfect collinearity
        x1 = np.random.randn(n)
        x2 = x1 * 2 + 5  # Perfect linear relationship
        
        df = pd.DataFrame({'pred1': x1, 'pred2': x2})
        
        # This should either raise an error or return very high VIF
        vif_results = calculate_vif(df)
        
        # At least one should have extremely high VIF or NaN
        assert (vif_results['pred1']['vif'] > 100.0 or 
                np.isnan(vif_results['pred1']['vif']) or
                vif_results['pred2']['vif'] > 100.0 or
                np.isnan(vif_results['pred2']['vif']))

    def test_calculate_vif_single_variable(self):
        """Test VIF calculation with a single predictor."""
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        
        df = pd.DataFrame({'pred1': x1})
        
        vif_results = calculate_vif(df)
        
        # Single variable should have VIF = 1.0
        assert vif_results['pred1']['vif'] == 1.0

    def test_calculate_vif_for_pair(self):
        """Test pairwise VIF calculation."""
        np.random.seed(42)
        n = 100
        
        # Low correlation
        x1 = np.random.randn(n)
        x2 = np.random.randn(n)
        
        vif_low = calculate_vif_for_pair(x1, x2)
        assert vif_low < 2.0  # Low correlation should give low VIF
        
        # High correlation
        x3 = x1 + np.random.randn(n) * 0.01
        
        vif_high = calculate_vif_for_pair(x1, x3)
        assert vif_high > 5.0  # High correlation should give high VIF

    def test_calculate_vif_flagging(self):
        """Test that high VIF values are properly flagged."""
        np.random.seed(42)
        n = 100
        
        x1 = np.random.randn(n)
        x2 = x1 + np.random.randn(n) * 0.01  # High correlation
        x3 = np.random.randn(n)  # Independent
        
        df = pd.DataFrame({'pred1': x1, 'pred2': x2, 'pred3': x3})
        
        vif_results = calculate_vif(df, threshold=5.0)
        
        # Check that high VIF variables are flagged
        assert vif_results['pred1']['flagged'] is True
        assert vif_results['pred2']['flagged'] is True
        assert vif_results['pred3']['flagged'] is False

    def test_calculate_vif_missing_values(self):
        """Test VIF calculation with missing values."""
        np.random.seed(42)
        n = 100
        
        x1 = np.random.randn(n)
        x2 = np.random.randn(n)
        
        # Introduce some missing values
        x1[5] = np.nan
        x2[10] = np.nan
        
        df = pd.DataFrame({'pred1': x1, 'pred2': x2})
        
        # Should handle missing values (drop or impute)
        vif_results = calculate_vif(df)
        
        # Should still produce results
        assert 'pred1' in vif_results
        assert 'pred2' in vif_results
        assert isinstance(vif_results['pred1']['vif'], (int, float))

    def test_calculate_vif_constant_variable(self):
        """Test VIF calculation with a constant variable."""
        np.random.seed(42)
        n = 100
        
        x1 = np.random.randn(n)
        x2 = np.ones(n)  # Constant variable
        
        df = pd.DataFrame({'pred1': x1, 'pred2': x2})
        
        # Should handle constant variables gracefully
        vif_results = calculate_vif(df)
        
        # At least one should be flagged or have high VIF
        assert 'pred1' in vif_results
        assert 'pred2' in vif_results

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
