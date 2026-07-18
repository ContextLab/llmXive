"""
Unit tests for collinearity diagnostics (VIF calculation).

Tests the functionality in code/modeling/collinearity.py
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modeling.collinearity import calculate_vif, flag_high_collinearity, VIF_THRESHOLD


class TestCalculateVIF:
    """Tests for the calculate_vif function."""
    
    def test_vif_single_feature(self):
        """Test VIF calculation with a single feature."""
        data = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        
        result = calculate_vif(data)
        
        assert len(result) == 1
        assert result.iloc[0]['feature'] == 'feature1'
        # VIF for a single feature should be 1.0 (no collinearity with other features)
        assert result.iloc[0]['vif'] == 1.0
    
    def test_vif_no_collinearity(self):
        """Test VIF calculation with uncorrelated features."""
        np.random.seed(42)
        n_samples = 100
        
        # Generate uncorrelated random features
        data = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'feature2': np.random.randn(n_samples),
            'feature3': np.random.randn(n_samples)
        })
        
        result = calculate_vif(data)
        
        assert len(result) == 3
        
        # With uncorrelated features, VIF should be close to 1.0
        # Allow some tolerance due to random variation
        for _, row in result.iterrows():
            assert 0.5 <= row['vif'] <= 3.0, f"VIF for {row['feature']} is {row['vif']}, expected ~1.0"
    
    def test_vif_high_collinearity(self):
        """Test VIF calculation with highly correlated features."""
        n_samples = 100
        
        # Create features with high correlation
        base = np.random.randn(n_samples)
        data = pd.DataFrame({
            'feature1': base,
            'feature2': base * 2 + np.random.randn(n_samples) * 0.1,  # Highly correlated
            'feature3': np.random.randn(n_samples)  # Independent
        })
        
        result = calculate_vif(data)
        
        assert len(result) == 3
        
        # feature1 and feature2 should have high VIF (> 5)
        vif_1 = result[result['feature'] == 'feature1']['vif'].values[0]
        vif_2 = result[result['feature'] == 'feature2']['vif'].values[0]
        
        assert vif_1 > 5.0, f"VIF for feature1 should be > 5, got {vif_1}"
        assert vif_2 > 5.0, f"VIF for feature2 should be > 5, got {vif_2}"
    
    def test_vif_perfect_collinearity(self):
        """Test VIF calculation with perfect collinearity."""
        n_samples = 100
        
        # Create perfectly collinear features
        base = np.random.randn(n_samples)
        data = pd.DataFrame({
            'feature1': base,
            'feature2': base * 2,  # Perfectly collinear
            'feature3': np.random.randn(n_samples)
        })
        
        result = calculate_vif(data)
        
        # feature1 and feature2 should have infinite VIF
        vif_1 = result[result['feature'] == 'feature1']['vif'].values[0]
        vif_2 = result[result['feature'] == 'feature2']['vif'].values[0]
        
        assert np.isinf(vif_1), f"VIF for feature1 should be infinite, got {vif_1}"
        assert np.isinf(vif_2), f"VIF for feature2 should be infinite, got {vif_2}"
    
    def test_vif_insufficient_samples(self):
        """Test VIF calculation with too few samples."""
        data = pd.DataFrame({
            'feature1': [1, 2],
            'feature2': [3, 4],
            'feature3': [5, 6]
        })
        
        # Should raise ValueError when samples <= features
        with pytest.raises(ValueError):
            calculate_vif(data)
    
    def test_vif_with_nan(self):
        """Test VIF calculation with NaN values."""
        data = pd.DataFrame({
            'feature1': [1, 2, 3, np.nan, 5, 6, 7, 8, 9, 10],
            'feature2': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        })
        
        # Should handle NaN by dropping rows
        result = calculate_vif(data)
        
        assert len(result) == 2
        assert all(pd.notna(result['vif']))
    
    def test_vif_specific_features(self):
        """Test VIF calculation for a subset of features."""
        data = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50),
            'feature3': np.random.randn(50),
            'feature4': np.random.randn(50)
        })
        
        # Calculate VIF for only feature1 and feature2
        result = calculate_vif(data, features=['feature1', 'feature2'])
        
        assert len(result) == 2
        assert set(result['feature']) == {'feature1', 'feature2'}
    
    def test_vif_output_format(self):
        """Test that VIF output has correct format."""
        data = pd.DataFrame({
            'feature1': np.random.randn(50),
            'feature2': np.random.randn(50)
        })
        
        result = calculate_vif(data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'feature' in result.columns
        assert 'vif' in result.columns
        assert result.shape[0] == 2


class TestFlagHighCollinearity:
    """Tests for the flag_high_collinearity function."""
    
    def test_flagging_default_threshold(self):
        """Test flagging with default threshold (5.0)."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4'],
            'vif': [1.0, 3.0, 5.0, 8.0]
        })
        
        result = flag_high_collinearity(vif_df)
        
        assert 'flagged' in result.columns
        assert result.loc[result['feature'] == 'f1', 'flagged'].values[0] == False
        assert result.loc[result['feature'] == 'f2', 'flagged'].values[0] == False
        assert result.loc[result['feature'] == 'f3', 'flagged'].values[0] == False  # Exactly 5.0 is not flagged
        assert result.loc[result['feature'] == 'f4', 'flagged'].values[0] == True
    
    def test_flagging_custom_threshold(self):
        """Test flagging with custom threshold."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3'],
            'vif': [3.0, 5.0, 7.0]
        })
        
        result = flag_high_collinearity(vif_df, threshold=6.0)
        
        assert result.loc[result['feature'] == 'f1', 'flagged'].values[0] == False
        assert result.loc[result['feature'] == 'f2', 'flagged'].values[0] == False
        assert result.loc[result['feature'] == 'f3', 'flagged'].values[0] == True
    
    def test_flagging_all_flagged(self):
        """Test when all features are flagged."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2'],
            'vif': [10.0, 15.0]
        })
        
        result = flag_high_collinearity(vif_df)
        
        assert result['flagged'].all()
    
    def test_flagging_none_flagged(self):
        """Test when no features are flagged."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3'],
            'vif': [1.0, 2.0, 3.0]
        })
        
        result = flag_high_collinearity(vif_df)
        
        assert not result['flagged'].any()
    
    def test_flagging_output_format(self):
        """Test that flagging output has correct format."""
        vif_df = pd.DataFrame({
            'feature': ['f1'],
            'vif': [5.0]
        })
        
        result = flag_high_collinearity(vif_df)
        
        assert isinstance(result, pd.DataFrame)
        assert 'feature' in result.columns
        assert 'vif' in result.columns
        assert 'flagged' in result.columns
        assert result['flagged'].dtype == bool


class TestVIFThreshold:
    """Tests for the VIF threshold constant."""
    
    def test_threshold_value(self):
        """Test that the default threshold is 5.0."""
        assert VIF_THRESHOLD == 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
