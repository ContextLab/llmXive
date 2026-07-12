"""
Tests for collinearity diagnostics.
"""
import pytest
import pandas as pd
import numpy as np
from features.collinearity import calculate_vif, get_collinear_features, remove_collinear_features


class TestCollinearity:
    """Test cases for collinearity functions."""
    
    def test_calculate_vif_basic(self):
        """Test basic VIF calculation."""
        # Create features with some correlation
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        
        vif_results = calculate_vif(X)
        
        assert len(vif_results) == 3
        assert all(isinstance(v, float) for v in vif_results.values())
    
    def test_high_vif_detection(self):
        """Test detection of high VIF values."""
        # Create highly correlated features
        np.random.seed(42)
        x1 = np.random.randn(100)
        X = pd.DataFrame({
            'feature1': x1,
            'feature2': x1 * 2 + 0.1 * np.random.randn(100),  # Highly correlated
            'feature3': np.random.randn(100)
        })
        
        vif_results = calculate_vif(X, threshold=5.0)
        
        # feature2 should have high VIF due to correlation with feature1
        assert vif_results['feature2'] > 5.0
    
    def test_get_collinear_features(self):
        """Test retrieval of collinear features."""
        vif_results = {
            'feature1': 2.0,
            'feature2': 8.5,
            'feature3': 1.5,
            'feature4': 12.0
        }
        
        collinear = get_collinear_features(vif_results, threshold=5.0)
        
        assert set(collinear) == {'feature2', 'feature4'}
    
    def test_remove_collinear_features(self):
        """Test removal of collinear features."""
        vif_results = {
            'feature1': 2.0,
            'feature2': 8.5,
            'feature3': 1.5
        }
        
        X = pd.DataFrame({
            'feature1': [1, 2, 3],
            'feature2': [4, 5, 6],
            'feature3': [7, 8, 9]
        })
        
        cleaned = remove_collinear_features(X, vif_results, threshold=5.0)
        
        assert 'feature2' not in cleaned.columns
        assert 'feature1' in cleaned.columns
        assert 'feature3' in cleaned.columns
    
    def test_empty_dataframe(self):
        """Test VIF calculation with empty DataFrame."""
        X = pd.DataFrame()
        
        with pytest.raises(ValueError, match="empty"):
            calculate_vif(X)