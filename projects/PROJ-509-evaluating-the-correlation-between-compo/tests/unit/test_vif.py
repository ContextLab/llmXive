"""
Unit tests for Variance Inflation Factor (VIF) calculation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from importance import calculate_vif, VIF_THRESHOLD

class TestVIF:
    def test_vif_no_collinearity(self):
        """Test VIF with orthogonal features (should be close to 1)."""
        np.random.seed(42)
        # Create orthogonal features
        n = 100
        x1 = np.random.randn(n)
        x2 = np.random.randn(n)
        x3 = np.random.randn(n)
        
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'x3': x3
        })
        
        vif_scores = calculate_vif(df)
        
        # VIF should be close to 1 for orthogonal features
        for feature, score in vif_scores.items():
            assert 1.0 <= score <= 2.0, f"VIF for {feature} is {score}, expected ~1.0"

    def test_vif_high_collinearity(self):
        """Test VIF with highly correlated features (should be > 10)."""
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        # Create x2 as almost identical to x1
        x2 = x1 + np.random.randn(n) * 0.01 
        
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2
        })
        
        vif_scores = calculate_vif(df)
        
        # Both should have high VIF
        for feature, score in vif_scores.items():
            assert score > VIF_THRESHOLD, f"VIF for {feature} is {score}, expected > {VIF_THRESHOLD}"

    def test_vif_empty_dataframe(self):
        """Test VIF with empty dataframe raises error."""
        df = pd.DataFrame()
        with pytest.raises(ValueError):
            calculate_vif(df)

    def test_vif_single_feature(self):
        """Test VIF with single feature (VIF should be 1)."""
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({'x1': np.random.randn(n)})
        
        vif_scores = calculate_vif(df)
        assert 'x1' in vif_scores
        assert abs(vif_scores['x1'] - 1.0) < 0.01