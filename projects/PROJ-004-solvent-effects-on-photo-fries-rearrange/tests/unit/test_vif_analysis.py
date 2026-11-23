import pytest
import pandas as pd
import numpy as np
from analysis.correlation import compute_vif, perform_vif_analysis

class TestVIFAnalysis:
    """Unit tests for VIF analysis functionality in correlation.py"""

    def test_compute_vif_two_features(self):
        """Test VIF calculation with two features"""
        # Create a DataFrame with two perfectly correlated features
        data = {
            'feature_a': [1, 2, 3, 4, 5],
            'feature_b': [2, 4, 6, 8, 10],  # Perfect correlation (r=1)
            'target': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        vif_scores = compute_vif(df, ['feature_a', 'feature_b'], 'target')
        
        # With perfect correlation, VIF should be very high (or infinite)
        assert 'feature_a' in vif_scores
        assert 'feature_b' in vif_scores
        # Since R^2 = 1, VIF = 1/(1-1) = inf
        assert vif_scores['feature_a'] == float('inf')
        assert vif_scores['feature_b'] == float('inf')

    def test_compute_vif_uncorrelated_features(self):
        """Test VIF calculation with uncorrelated features"""
        # Create a DataFrame with uncorrelated features
        np.random.seed(42)
        data = {
            'feature_a': np.random.randn(100),
            'feature_b': np.random.randn(100),
            'target': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        
        vif_scores = compute_vif(df, ['feature_a', 'feature_b'], 'target')
        
        # With uncorrelated features, VIF should be close to 1
        assert 1.0 <= vif_scores['feature_a'] <= 2.0
        assert 1.0 <= vif_scores['feature_b'] <= 2.0

    def test_compute_vif_moderate_correlation(self):
        """Test VIF calculation with moderately correlated features"""
        # Create a DataFrame with moderately correlated features
        np.random.seed(42)
        feature_a = np.random.randn(100)
        feature_b = 0.7 * feature_a + 0.3 * np.random.randn(100)  # Moderate correlation
        
        data = {
            'feature_a': feature_a,
            'feature_b': feature_b,
            'target': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        
        vif_scores = compute_vif(df, ['feature_a', 'feature_b'], 'target')
        
        # With moderate correlation, VIF should be between 2 and 5
        assert 2.0 < vif_scores['feature_a'] < 5.0
        assert 2.0 < vif_scores['feature_b'] < 5.0

    def test_perform_vif_analysis_insufficient_features(self):
        """Test VIF analysis with insufficient features"""
        data = {
            'feature_a': [1, 2, 3, 4, 5],
            'target': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        result = perform_vif_analysis(df)
        
        assert result['status'] == 'insufficient_data'
        assert len(result['available_features']) < 2
        assert 'Cannot perform VIF analysis' in result['interpretation']

    def test_perform_vif_analysis_success(self):
        """Test successful VIF analysis with sufficient features"""
        # Create a DataFrame with multiple features
        np.random.seed(42)
        feature_a = np.random.randn(50)
        feature_b = 0.5 * feature_a + 0.5 * np.random.randn(50)
        feature_c = np.random.randn(50)
        
        data = {
            'feature_a': feature_a,
            'feature_b': feature_b,
            'feature_c': feature_c,
            'lifetime_mean': np.random.randn(50)
        }
        df = pd.DataFrame(data)
        
        result = perform_vif_analysis(df)
        
        assert result['status'] == 'success'
        assert len(result['vif_scores']) >= 2
        assert 'interpretation' in result
        assert 'recommendation' in result

    def test_vif_with_constant_feature(self):
        """Test VIF calculation with a constant feature"""
        data = {
            'feature_a': [1, 1, 1, 1, 1],  # Constant
            'feature_b': [2, 4, 6, 8, 10],
            'target': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        vif_scores = compute_vif(df, ['feature_a', 'feature_b'], 'target')
        
        # Constant feature should result in infinite VIF
        assert vif_scores['feature_a'] == float('inf')
        assert vif_scores['feature_b'] > 1.0

    def test_vif_interpretation_high_collinearity(self):
        """Test VIF interpretation for high collinearity"""
        # Create features with high collinearity
        np.random.seed(42)
        feature_a = np.random.randn(50)
        feature_b = 0.95 * feature_a + 0.05 * np.random.randn(50)  # High correlation
        
        data = {
            'feature_a': feature_a,
            'feature_b': feature_b,
            'target': np.random.randn(50)
        }
        df = pd.DataFrame(data)
        
        result = perform_vif_analysis(df)
        
        assert result['status'] == 'success'
        assert len(result['high_vif_features']) > 0
        assert 'High multicollinearity' in result['interpretation']

    def test_vif_interpretation_low_collinearity(self):
        """Test VIF interpretation for low collinearity"""
        # Create features with low collinearity
        np.random.seed(42)
        feature_a = np.random.randn(50)
        feature_b = np.random.randn(50)
        feature_c = np.random.randn(50)
        
        data = {
            'feature_a': feature_a,
            'feature_b': feature_b,
            'feature_c': feature_c,
            'lifetime_mean': np.random.randn(50)
        }
        df = pd.DataFrame(data)
        
        result = perform_vif_analysis(df)
        
        assert result['status'] == 'success'
        assert len(result['low_vif_features']) > 0
        assert 'Low multicollinearity' in result['interpretation'] or 'distinct predictors' in result['interpretation']