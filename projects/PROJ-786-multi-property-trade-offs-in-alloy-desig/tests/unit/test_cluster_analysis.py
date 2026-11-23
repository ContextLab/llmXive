"""
Unit tests for cluster_analysis.py
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.cluster_analysis import (
    get_feature_columns,
    perform_kmeans_clustering,
    calculate_cluster_correlations,
    identify_decoupled_region
)


def test_get_feature_columns():
    """Test feature column detection."""
    df = pd.DataFrame({
        'composition': ['Fe', 'Ni'],
        'bulk_modulus': [100, 120],
        'shear_modulus': [50, 60],
        'element_Fe': [0.5, 0.0],
        'element_Ni': [0.5, 1.0],
        'element_Cu': [0.0, 0.0]
    })
    
    cols = get_feature_columns(df)
    assert 'element_Fe' in cols
    assert 'element_Ni' in cols
    assert 'element_Cu' in cols
    assert 'bulk_modulus' not in cols
    assert 'shear_modulus' not in cols
    assert 'composition' not in cols


def test_perform_kmeans_clustering():
    """Test K-Means clustering execution."""
    np.random.seed(42)
    df = pd.DataFrame({
        'element_A': np.random.rand(100),
        'element_B': np.random.rand(100),
        'element_C': np.random.rand(100),
        'bulk_modulus': np.random.rand(100),
        'shear_modulus': np.random.rand(100)
    })
    
    feature_cols = ['element_A', 'element_B', 'element_C']
    df_clusters, kmeans, scaler = perform_kmeans_clustering(df, feature_cols, k=3)
    
    assert 'cluster_id' in df_clusters.columns
    assert df_clusters['cluster_id'].nunique() == 3
    assert all(df_clusters['cluster_id'].isin([0, 1, 2]))
    assert kmeans is not None
    assert scaler is not None


def test_calculate_cluster_correlations():
    """Test correlation calculation per cluster."""
    df = pd.DataFrame({
        'cluster_id': [0, 0, 0, 1, 1, 1],
        'bulk_modulus': [10, 20, 30, 100, 200, 300],
        'shear_modulus': [5, 10, 15, 50, 100, 150]
    })
    
    results = calculate_cluster_correlations(df)
    
    assert len(results) == 2
    assert 0 in results['cluster_id'].values
    assert 1 in results['cluster_id'].values
    
    # Cluster 0: Perfect positive correlation
    corr_0 = results[results['cluster_id'] == 0]['correlation'].values[0]
    assert np.isclose(corr_0, 1.0)
    
    # Cluster 1: Perfect positive correlation
    corr_1 = results[results['cluster_id'] == 1]['correlation'].values[0]
    assert np.isclose(corr_1, 1.0)


def test_identify_decoupled_region():
    """Test identification of minimum correlation cluster."""
    results = pd.DataFrame({
        'cluster_id': [0, 1, 2],
        'size': [10, 20, 15],
        'correlation': [0.8, 0.1, 0.5],
        'mean_bulk': [100, 200, 150],
        'mean_shear': [50, 100, 75]
    })
    
    decoupled = identify_decoupled_region(results)
    
    assert decoupled['cluster_id'] == 1
    assert np.isclose(decoupled['correlation'], 0.1)
    assert decoupled['size'] == 20
