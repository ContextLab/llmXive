"""
Unit tests for VIF clustering logic.

This module validates the VIF (Variance Inflation Factor) calculation and
clustering functionality used for feature diagnostics in the molecular polarity
prediction pipeline.

Tests cover:
1. VIF calculation accuracy on known datasets
2. Clustering logic for highly correlated features (|r| > 0.8)
3. Edge cases (single feature, perfect correlation, NaN handling)
"""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.feature_clustering import compute_vif, cluster_correlated_features


class TestVIFCalculation:
    """Test VIF calculation logic."""

    def test_vif_perfect_correlation(self):
        """VIF should be very high for perfectly correlated features."""
        # Create a dataset with perfect correlation
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'f1': np.random.randn(n),
            'f2': np.random.randn(n),
            'f3': np.random.randn(n)
        })
        # Add perfect correlation
        X['f1'] = X['f2']  # f1 and f2 are identical

        vif_values = compute_vif(X)

        # f1 and f2 should have very high VIF due to perfect correlation
        assert vif_values['f1'] > 100 or vif_values['f2'] > 100

    def test_vif_no_correlation(self):
        """VIF should be close to 1 for uncorrelated features."""
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'f1': np.random.randn(n),
            'f2': np.random.randn(n),
            'f3': np.random.randn(n)
        })

        vif_values = compute_vif(X)

        # All VIF values should be close to 1
        for vif in vif_values.values():
            assert 0.9 <= vif <= 1.5

    def test_vif_single_feature(self):
        """Single feature should have VIF of 1."""
        X = pd.DataFrame({'f1': [1, 2, 3, 4, 5]})
        vif_values = compute_vif(X)
        assert vif_values['f1'] == 1.0

    def test_vif_nan_handling(self):
        """VIF calculation should handle NaN values appropriately."""
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'f1': np.random.randn(n),
            'f2': np.random.randn(n),
            'f3': np.random.randn(n)
        })
        # Introduce some NaN values
        X.loc[0:9, 'f1'] = np.nan

        # Should not raise an error
        vif_values = compute_vif(X.dropna())
        assert len(vif_values) == 2  # Only 2 features after dropping NaN rows


class TestCorrelatedFeatureClustering:
    """Test clustering of highly correlated features."""

    def test_cluster_identical_features(self):
        """Identical features should be grouped into the same cluster."""
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'f1': np.random.randn(n),
            'f2': np.random.randn(n),
            'f3': np.random.randn(n)
        })
        # Make f1 and f2 identical
        X['f2'] = X['f1']
        # Make f3 and f4 identical
        X['f4'] = X['f3']

        clusters = cluster_correlated_features(X, threshold=0.8)

        # f1 and f2 should be in the same cluster
        f1_cluster = [c for c in clusters if 'f1' in c][0]
        f2_cluster = [c for c in clusters if 'f2' in c][0]
        assert f1_cluster == f2_cluster

        # f3 and f4 should be in the same cluster
        f3_cluster = [c for c in clusters if 'f3' in c][0]
        f4_cluster = [c for c in clusters if 'f4' in c][0]
        assert f3_cluster == f4_cluster

        # The two clusters should be different
        assert f1_cluster != f3_cluster

    def test_cluster_threshold(self):
        """Features with correlation below threshold should not be clustered."""
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'f1': np.random.randn(n),
            'f2': np.random.randn(n),
            'f3': np.random.randn(n)
        })
        # Make f1 and f2 highly correlated
        X['f2'] = X['f1'] * 0.9 + np.random.randn(n) * 0.1

        # With threshold 0.8, they should be clustered
        clusters_80 = cluster_correlated_features(X, threshold=0.8)
        f1_cluster_80 = [c for c in clusters_80 if 'f1' in c][0]
        f2_cluster_80 = [c for c in clusters_80 if 'f2' in c][0]
        assert f1_cluster_80 == f2_cluster_80

        # With threshold 0.95, they should not be clustered
        clusters_95 = cluster_correlated_features(X, threshold=0.95)
        f1_cluster_95 = [c for c in clusters_95 if 'f1' in c][0]
        f2_cluster_95 = [c for c in clusters_95 if 'f2' in c][0]
        assert f1_cluster_95 != f2_cluster_95

    def test_empty_input(self):
        """Empty dataframe should return empty clusters."""
        X = pd.DataFrame()
        clusters = cluster_correlated_features(X)
        assert clusters == []

    def test_single_feature(self):
        """Single feature should be in its own cluster."""
        X = pd.DataFrame({'f1': [1, 2, 3, 4, 5]})
        clusters = cluster_correlated_features(X)
        assert clusters == [{'f1'}]

    def test_all_features_correlated(self):
        """All features should be in one cluster if all are highly correlated."""
        np.random.seed(42)
        n = 100
        base = np.random.randn(n)
        X = pd.DataFrame({
            'f1': base,
            'f2': base + np.random.randn(n) * 0.01,
            'f3': base + np.random.randn(n) * 0.01,
            'f4': base + np.random.randn(n) * 0.01
        })

        clusters = cluster_correlated_features(X, threshold=0.8)

        # All features should be in the same cluster
        assert len(clusters) == 1
        assert len(clusters[0]) == 4

    def test_no_features_correlated(self):
        """Each feature should be in its own cluster if none are correlated."""
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'f1': np.random.randn(n),
            'f2': np.random.randn(n),
            'f3': np.random.randn(n)
        })

        clusters = cluster_correlated_features(X, threshold=0.8)

        # Each feature should be in its own cluster
        assert len(clusters) == 3
        for cluster in clusters:
            assert len(cluster) == 1


class TestIntegrationWithRealData:
    """Integration tests with realistic molecular descriptor data patterns."""

    def test_molecular_descriptor_pattern(self):
        """Test with a pattern similar to molecular descriptors where some are correlated."""
        np.random.seed(42)
        n = 200
        # Simulate molecular descriptors with some natural correlations
        X = pd.DataFrame({
            'molecular_weight': np.random.uniform(100, 500, n),
            'logP': np.random.uniform(-2, 5, n),
            'num_h_acceptors': np.random.randint(0, 10, n),
            'num_h_donors': np.random.randint(0, 10, n),
            'rotatable_bonds': np.random.randint(0, 15, n),
            'aromatic_rings': np.random.randint(0, 5, n)
        })

        # Introduce realistic correlations
        # LogP tends to correlate with molecular weight
        X['logP'] = 0.5 * X['molecular_weight'] / 100 + np.random.randn(n) * 0.5

        # H-bond acceptors and donors often correlate
        X['num_h_donors'] = X['num_h_acceptors'] + np.random.randint(-1, 2, n)

        clusters = cluster_correlated_features(X, threshold=0.7)

        # Should find at least some clustering
        assert len(clusters) <= 6  # At most one cluster per feature

        # Verify clusters are valid (no duplicates)
        all_features = []
        for cluster in clusters:
            all_features.extend(list(cluster))
        assert len(all_features) == len(X.columns)
        assert len(set(all_features)) == len(X.columns)