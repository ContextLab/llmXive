import os
import json
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
import networkx as nx

# Import the module under test using the API surface
from motifs import (
    count_motifs,
    generate_null_model,
    compute_z_scores,
    get_motif_id
)

@pytest.fixture
def small_binary_graph():
    """Create a small binary adjacency matrix for testing."""
    # 4-node graph
    adj = np.array([
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [1, 0, 0, 1],
        [0, 1, 0, 0]
    ], dtype=float)
    return adj

def test_count_motifs_returns_dict_with_all_motifs(small_binary_graph):
    """Contract: Verify count_motifs returns a dict with counts for all directed 3-node motifs."""
    # There are 13 directed 3-node motifs
    result = count_motifs(small_binary_graph)
    
    assert isinstance(result, dict)
    # Check that all 13 motif types are present
    for i in range(13):
        motif_id = get_motif_id(i)
        assert motif_id in result, f"Missing motif {motif_id}"

def test_count_motifs_sum_equals_theoretical_total(small_binary_graph):
    """Contract: Verify sum of counts equals theoretical total for complete graph."""
    # For a complete directed graph with N nodes, number of 3-node subgraphs is C(N,3)
    # But for a general graph, we count all induced 3-node subgraphs
    n = small_binary_graph.shape[0]
    
    # The theoretical total number of 3-node subgraphs in a graph with n nodes is C(n, 3)
    # However, count_motifs counts all possible 3-node combinations
    from itertools import combinations
    theoretical_combinations = len(list(combinations(range(n), 3)))
    
    result = count_motifs(small_binary_graph)
    total_counted = sum(result.values())
    
    # Each 3-node combination should be counted exactly once
    assert total_counted == theoretical_combinations

def test_count_motifs_values_non_negative(small_binary_graph):
    """Verify all motif counts are non-negative."""
    result = count_motifs(small_binary_graph)
    
    for motif_id, count in result.items():
        assert count >= 0, f"Negative count for {motif_id}"

def test_generate_null_model_preserves_degree_distribution(small_binary_graph):
    """Contract: Verify generate_null_model preserves degree distribution."""
    iterations = 100
    
    # Compute original degrees
    original_in_degrees = np.sum(small_binary_graph, axis=0)
    original_out_degrees = np.sum(small_binary_graph, axis=1)
    
    # Generate null model
    null_adj = generate_null_model(small_binary_graph, iterations=iterations)
    
    # Compute null degrees
    null_in_degrees = np.sum(null_adj, axis=0)
    null_out_degrees = np.sum(null_adj, axis=1)
    
    # Check that degrees are preserved (within floating point tolerance)
    assert np.allclose(original_in_degrees, null_in_degrees, atol=1e-6)
    assert np.allclose(original_out_degrees, null_out_degrees, atol=1e-6)

def test_generate_null_model_returns_binary_matrix(small_binary_graph):
    """Verify null model returns a binary matrix."""
    null_adj = generate_null_model(small_binary_graph, iterations=10)
    
    # Check that all values are 0 or 1
    assert np.all((null_adj == 0) | (null_adj == 1))
    assert null_adj.shape == small_binary_graph.shape

def test_compute_z_scores_correct_formula():
    """Contract: Verify z-score formula: z = (observed - mean_null) / std_null."""
    # Create mock counts
    observed_counts = {
        'motif_0': 10,
        'motif_1': 5,
        'motif_2': 8
    }
    
    # Create mock null counts (multiple iterations)
    null_counts = {
        'motif_0': [8, 12, 9, 11, 10],
        'motif_1': [4, 6, 5, 4, 5],
        'motif_2': [7, 9, 8, 7, 9]
    }
    
    result = compute_z_scores(observed_counts, null_counts)
    
    # Manually compute expected z-score for motif_0
    # observed = 10, mean = (8+12+9+11+10)/5 = 10, std = sqrt(((8-10)^2 + ...)/4)
    expected_mean = np.mean(null_counts['motif_0'])
    expected_std = np.std(null_counts['motif_0'], ddof=1)  # Sample std
    expected_z = (observed_counts['motif_0'] - expected_mean) / expected_std
    
    assert isinstance(result, dict)
    assert 'motif_0' in result
    assert np.isclose(result['motif_0'], expected_z)

def test_compute_z_scores_returns_all_motifs():
    """Verify z-scores are computed for all motifs."""
    observed_counts = {f'motif_{i}': i for i in range(13)}
    null_counts = {f'motif_{i}': [i] * 5 for i in range(13)}
    
    result = compute_z_scores(observed_counts, null_counts)
    
    assert len(result) == 13
    for i in range(13):
        assert f'motif_{i}' in result

def test_get_motif_id_returns_valid_string():
    """Verify get_motif_id returns a valid motif identifier."""
    for i in range(13):
        motif_id = get_motif_id(i)
        assert isinstance(motif_id, str)
        assert motif_id.startswith('motif_')
        assert int(motif_id.split('_')[1]) == i
