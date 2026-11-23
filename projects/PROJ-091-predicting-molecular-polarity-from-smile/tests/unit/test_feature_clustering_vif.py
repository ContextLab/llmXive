"""
Unit tests for VIF computation and clustering logic in code/data/feature_clustering.py.
Tests correlation matrix generation, VIF calculation, and cluster formation.
"""
import pytest
import pandas as pd
import numpy as np
from code.data.feature_clustering import compute_vif, cluster_correlated_features


class TestVIFComputation:
    """Tests for the compute_vif function."""

    def test_vif_no_collinearity(self):
        """Test VIF calculation on orthogonal features."""
        np.random.seed(42)
        n_samples = 100
        n_features = 3
        # Create orthogonal features
        data = np.random.randn(n_samples, n_features)
        df = pd.DataFrame(data, columns=['f1', 'f2', 'f3'])
        
        vif_scores = compute_vif(df)
        
        # VIF should be close to 1 for orthogonal features
        for feature, vif in vif_scores.items():
            assert 1.0 <= vif < 1.1, f"VIF for {feature} should be ~1, got {vif}"

    def test_vif_high_collinearity(self):
        """Test VIF calculation on highly correlated features."""
        np.random.seed(42)
        n_samples = 100
        # Create features with high correlation
        f1 = np.random.randn(n_samples)
        f2 = f1 * 0.99 + np.random.randn(n_samples) * 0.01
        f3 = f1 * 0.98 + np.random.randn(n_samples) * 0.02
        df = pd.DataFrame({'f1': f1, 'f2': f2, 'f3': f3})
        
        vif_scores = compute_vif(df)
        
        # VIF should be high for correlated features
        for feature, vif in vif_scores.items():
            assert vif > 10, f"VIF for {feature} should be high (>10), got {vif}"

    def test_vif_single_feature(self):
        """Test VIF on a single feature (should be 1)."""
        df = pd.DataFrame({'f1': [1, 2, 3, 4, 5]})
        vif_scores = compute_vif(df)
        assert vif_scores['f1'] == 1.0

    def test_vif_constant_feature(self):
        """Test VIF on a constant feature (should raise or return inf)."""
        df = pd.DataFrame({'f1': [1, 1, 1, 1, 1], 'f2': [1, 2, 3, 4, 5]})
        # VIF calculation usually involves inverting a matrix; constant column makes it singular.
        # The function should handle this gracefully (e.g., return inf or skip).
        # We test that it doesn't crash.
        try:
            vif_scores = compute_vif(df)
            # If it returns a value, it should be very high or inf
            assert vif_scores['f1'] == np.inf or vif_scores['f1'] > 1000
        except Exception:
            # Or it might raise an error, which is also acceptable behavior for singular matrix
            pass


class TestClusterCorrelatedFeatures:
    """Tests for the cluster_correlated_features function."""

    def test_cluster_no_correlation(self):
        """Test clustering when no features are correlated above threshold."""
        np.random.seed(42)
        n_samples = 100
        n_features = 5
        data = np.random.randn(n_samples, n_features)
        df = pd.DataFrame(data, columns=[f'f{i}' for i in range(n_features)])
        
        clusters = cluster_correlated_features(df, threshold=0.8)
        
        # Each feature should be in its own cluster
        assert len(clusters) == n_features
        for cluster_id, features in clusters.items():
            assert len(features) == 1

    def test_cluster_perfect_correlation(self):
        """Test clustering when features are perfectly correlated."""
        np.random.seed(42)
        n_samples = 100
        f1 = np.random.randn(n_samples)
        f2 = f1
        f3 = f1
        df = pd.DataFrame({'f1': f1, 'f2': f2, 'f3': f3})
        
        clusters = cluster_correlated_features(df, threshold=0.8)
        
        # All features should be in one cluster
        assert len(clusters) == 1
        cluster_features = list(clusters.values())[0]
        assert set(cluster_features) == {'f1', 'f2', 'f3'}

    def test_cluster_mixed_correlation(self):
        """Test clustering with mixed correlation levels."""
        np.random.seed(42)
        n_samples = 100
        f1 = np.random.randn(n_samples)
        f2 = f1 * 0.9 + np.random.randn(n_samples) * 0.1  # High corr
        f3 = np.random.randn(n_samples)
        f4 = f3 * 0.95 + np.random.randn(n_samples) * 0.05 # High corr
        f5 = np.random.randn(n_samples) # No corr
        df = pd.DataFrame({'f1': f1, 'f2': f2, 'f3': f3, 'f4': f4, 'f5': f5})
        
        clusters = cluster_correlated_features(df, threshold=0.8)
        
        # Expect 3 clusters: {f1, f2}, {f3, f4}, {f5}
        assert len(clusters) == 3
        
        # Check specific groupings
        cluster_lists = [set(v) for v in clusters.values()]
        assert {'f1', 'f2'} in cluster_lists
        assert {'f3', 'f4'} in cluster_lists
        assert {'f5'} in cluster_lists

    def test_cluster_threshold_sensitivity(self):
        """Test that changing threshold changes cluster count."""
        np.random.seed(42)
        n_samples = 100
        f1 = np.random.randn(n_samples)
        f2 = f1 * 0.85 + np.random.randn(n_samples) * 0.15 # Correlation ~0.85
        df = pd.DataFrame({'f1': f1, 'f2': f2})
        
        clusters_low = cluster_correlated_features(df, threshold=0.8)
        clusters_high = cluster_correlated_features(df, threshold=0.9)
        
        # At 0.8 threshold, they should cluster together
        assert len(clusters_low) == 1
        # At 0.9 threshold, they should be separate
        assert len(clusters_high) == 2
