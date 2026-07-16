"""Unit tests for the stats_engine module."""
import pytest
import pandas as pd
import numpy as np
from stats_engine import (
    compute_correlation,
    construct_graph,
    calculate_stats,
    generate_null_distribution,
    generate_synthetic_dataset,
    validate_null_model,
)


def test_compute_correlation_pearson():
    """Test Pearson correlation computation."""
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [2, 4, 6, 8, 10],
    })
    corr = compute_correlation(df, method="pearson")
    assert corr.loc['A', 'B'] == 1.0


def test_construct_graph_threshold():
    """Test graph construction with threshold."""
    corr = pd.DataFrame({
        'A': [1.0, 0.5, 0.1],
        'B': [0.5, 1.0, 0.8],
        'C': [0.1, 0.8, 1.0],
    })
    G = construct_graph(corr, threshold=0.3)
    assert G.number_of_nodes() == 3
    assert G.number_of_edges() == 2  # A-B and B-C


def test_calculate_stats_empty_graph():
    """Test stats calculation on empty graph."""
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(['A', 'B'])
    stats = calculate_stats(G)
    assert stats['edge_density'] == 0.0
    assert stats['avg_clustering'] == 0.0


def test_generate_synthetic_dataset():
    """Test synthetic dataset generation."""
    df = generate_synthetic_dataset(n_samples=100, n_vars=5, random_seed=42)
    assert df.shape == (100, 5)
    # Check that correlations are near zero
    corr = compute_correlation(df)
    # Diagonal should be 1, off-diagonal near 0
    for i in range(5):
        for j in range(5):
            if i != j:
                assert abs(corr.iloc[i, j]) < 0.2


def test_permutation_preserves_marginals():
    """Verify that permutation preserves marginal distributions."""
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50],
    })
    # Permute A
    permuted_A = np.random.permutation(df['A'])
    # Marginal distribution (sorted values) should be identical
    assert sorted(permuted_A) == sorted(df['A'].values)


def test_validate_null_model_synthetic():
    """Validate null model with synthetic uncorrelated data."""
    df = generate_synthetic_dataset(n_samples=500, n_vars=20, random_seed=42)
    observed_stats = calculate_stats(construct_graph(compute_correlation(df), 0.3))

    def stats_func(data):
        return calculate_stats(construct_graph(compute_correlation(data), 0.3))

    null_dist = generate_null_distribution(df, n_permutations=100, stats_func=stats_func, random_seed=42)
    p_values = validate_null_model(observed_stats, null_dist)

    # For uncorrelated data, p-values should be > 0.05 (not significant)
    for stat, p_val in p_values.items():
        assert p_val > 0.05, f"Statistic {stat} has p-value {p_val} <= 0.05"
