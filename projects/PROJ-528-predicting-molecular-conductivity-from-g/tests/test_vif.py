"""
Unit tests for VIF calculation and thresholding.

These tests verify the Variance Inflation Factor (VIF) calculation logic
and the thresholding mechanism for feature exclusion.
"""
import pytest
import numpy as np
import pandas as pd
from typing import Tuple, List
from statsmodels.stats.outliers_influence import variance_inflation_factor
from code.config import VIF_THRESHOLD


def compute_vif_for_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute VIF for each feature in a DataFrame.
    
    Args:
        df: DataFrame containing only numeric features (no target column).
        
    Returns:
        DataFrame with columns 'feature' and 'vif'.
    """
    if df.empty:
        return pd.DataFrame(columns=['feature', 'vif'])
    
    vif_data = []
    for i, col in enumerate(df.columns):
        # Calculate VIF for each column
        vif = variance_inflation_factor(df.values, i)
        vif_data.append({'feature': col, 'vif': vif})
    
    return pd.DataFrame(vif_data)


def filter_features_by_vif(df: pd.DataFrame, threshold: float = VIF_THRESHOLD) -> List[str]:
    """
    Identify features with VIF above the threshold.
    
    Args:
        df: DataFrame containing only numeric features.
        threshold: VIF threshold for exclusion (default from config).
        
    Returns:
        List of feature names that exceed the threshold.
    """
    if df.empty:
        return []
    
    vif_df = compute_vif_for_dataframe(df)
    high_vif_features = vif_df[vif_df['vif'] > threshold]['feature'].tolist()
    return high_vif_features


class TestVIFCalculation:
    """Tests for VIF calculation logic."""
    
    def test_vif_perfectly_uncorrelated_features(self):
        """VIF should be 1.0 for perfectly uncorrelated features."""
        # Create orthogonal features
        n_samples = 100
        np.random.seed(42)
        data = {
            'feature_a': np.random.randn(n_samples),
            'feature_b': np.random.randn(n_samples),
            'feature_c': np.random.randn(n_samples)
        }
        df = pd.DataFrame(data)
        
        vif_df = compute_vif_for_dataframe(df)
        
        # All VIFs should be close to 1.0
        assert all(vif_df['vif'] > 0.9)
        assert all(vif_df['vif'] < 1.1)
    
    def test_vif_perfectly_correlated_features(self):
        """VIF should be infinite (or very large) for perfectly correlated features."""
        n_samples = 100
        np.random.seed(42)
        base = np.random.randn(n_samples)
        data = {
            'feature_a': base,
            'feature_b': base * 2 + 5,  # Perfectly correlated
            'feature_c': np.random.randn(n_samples)  # Uncorrelated
        }
        df = pd.DataFrame(data)
        
        vif_df = compute_vif_for_dataframe(df)
        
        # feature_a and feature_b should have very high VIF
        high_vif_features = vif_df[vif_df['vif'] > 100]['feature'].tolist()
        assert 'feature_a' in high_vif_features or 'feature_b' in high_vif_features
    
    def test_vif_with_constant_feature(self):
        """VIF calculation should handle constant features gracefully."""
        n_samples = 100
        np.random.seed(42)
        data = {
            'feature_a': np.random.randn(n_samples),
            'feature_b': np.ones(n_samples),  # Constant
            'feature_c': np.random.randn(n_samples)
        }
        df = pd.DataFrame(data)
        
        # This should not crash, though statsmodels might return NaN or inf
        vif_df = compute_vif_for_dataframe(df)
        assert len(vif_df) == 3
        assert all(vif_df['feature'].isin(['feature_a', 'feature_b', 'feature_c']))


class TestVIFThresholding:
    """Tests for VIF thresholding logic."""
    
    def test_threshold_filter_with_low_vif(self):
        """No features should be excluded when all VIFs are below threshold."""
        n_samples = 100
        np.random.seed(42)
        data = {
            'feature_a': np.random.randn(n_samples),
            'feature_b': np.random.randn(n_samples),
            'feature_c': np.random.randn(n_samples)
        }
        df = pd.DataFrame(data)
        
        excluded = filter_features_by_vif(df, threshold=VIF_THRESHOLD)
        assert len(excluded) == 0
    
    def test_threshold_filter_with_high_vif(self):
        """Features with VIF > threshold should be identified."""
        n_samples = 100
        np.random.seed(42)
        base = np.random.randn(n_samples)
        data = {
            'feature_a': base,
            'feature_b': base * 2 + 5,  # Highly correlated
            'feature_c': np.random.randn(n_samples)
        }
        df = pd.DataFrame(data)
        
        excluded = filter_features_by_vif(df, threshold=VIF_THRESHOLD)
        
        # At least one of the correlated features should be excluded
        assert len(excluded) >= 1
        assert all(f in excluded for f in ['feature_a', 'feature_b'] if f in df.columns)
    
    def test_threshold_filter_empty_dataframe(self):
        """Should return empty list for empty DataFrame."""
        df = pd.DataFrame()
        excluded = filter_features_by_vif(df)
        assert excluded == []
    
    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        n_samples = 100
        np.random.seed(42)
        # Create features with moderate correlation
        base = np.random.randn(n_samples)
        data = {
            'feature_a': base,
            'feature_b': base * 0.8 + np.random.randn(n_samples) * 0.2,  # Correlated
            'feature_c': np.random.randn(n_samples)
        }
        df = pd.DataFrame(data)
        
        # With low threshold, more features should be excluded
        excluded_low = filter_features_by_vif(df, threshold=5.0)
        # With high threshold, fewer features should be excluded
        excluded_high = filter_features_by_vif(df, threshold=50.0)
        
        assert len(excluded_low) >= len(excluded_high)


class TestIntegration:
    """Integration tests for VIF workflow."""
    
    def test_iterative_exclusion_workflow(self):
        """Test the iterative exclusion of high VIF features."""
        n_samples = 100
        np.random.seed(42)
        base1 = np.random.randn(n_samples)
        base2 = np.random.randn(n_samples)
        # Create a set of highly correlated features
        data = {
            'f1': base1,
            'f2': base1 * 2,
            'f3': base1 * 3,
            'f4': base2,
            'f5': base2 * 2,
            'f6': np.random.randn(n_samples)  # Independent
        }
        df = pd.DataFrame(data)
        
        # Iteratively exclude features until all VIFs are below threshold
        remaining_features = list(df.columns)
        iterations = 0
        max_iterations = 10
        
        while iterations < max_iterations:
            current_df = df[remaining_features]
            high_vif = filter_features_by_vif(current_df, threshold=VIF_THRESHOLD)
            
            if not high_vif:
                break
            
            # Remove the feature with the highest VIF
            vif_df = compute_vif_for_dataframe(current_df)
            highest_vif_feature = vif_df.loc[vif_df['vif'].idxmax(), 'feature']
            remaining_features.remove(highest_vif_feature)
            iterations += 1
        
        # Verify that no remaining features have VIF > threshold
        final_df = df[remaining_features]
        final_vif_df = compute_vif_for_dataframe(final_df)
        
        assert all(final_vif_df['vif'] <= VIF_THRESHOLD)
        assert len(remaining_features) < len(df.columns)  # Some features should have been removed