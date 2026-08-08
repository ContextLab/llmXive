"""
tests/unit/test_motifs.py

Unit tests for motif enumeration and null model generation.
"""

import numpy as np
import networkx as nx
import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from motifs import count_motifs, generate_null_model, compute_motif_z_scores

def test_count_motifs_small_graph():
    """Test motif counting on a small, known graph."""
    # Create a simple graph: 0->1, 1->2, 2->0 (a directed triangle)
    adj = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0]
    ])
    
    counts = count_motifs(adj)
    
    # A directed triangle is one specific motif.
    # There should be exactly 1 motif found (the triangle itself).
    assert len(counts) == 1
    # The count should be 1
    assert sum(counts.values()) == 1

def test_count_motifs_empty():
    """Test motif counting on a graph with no edges."""
    adj = np.zeros((4, 4), dtype=int)
    counts = count_motifs(adj)
    assert counts == {}

def test_count_motifs_incomplete():
    """Test on a graph with < 3 nodes."""
    adj = np.array([[0, 1], [1, 0]])
    counts = count_motifs(adj)
    assert counts == {}

def test_generate_null_model_preserves_degree():
    """Test that Maslov-Sneppen preserves in/out degrees."""
    # Create a graph with known degrees
    adj = np.array([
        [0, 1, 1],
        [1, 0, 0],
        [0, 1, 0]
    ])
    
    G = nx.DiGraph(adj)
    in_deg_orig = dict(G.in_degree())
    out_deg_orig = dict(G.out_degree())
    
    nulls = generate_null_model(adj, iterations=5)
    assert len(nulls) == 5
    
    for null_adj in nulls:
        G_null = nx.DiGraph(null_adj)
        in_deg_null = dict(G_null.in_degree())
        out_deg_null = dict(G_null.out_degree())
        
        assert in_deg_orig == in_deg_null
        assert out_deg_orig == out_deg_null

def test_compute_z_scores():
    """Test z-score computation."""
    observed = {"key1": 10}
    # Create null models that have counts close to 10
    # Mock null counts
    null_counts = [
        {"key1": 9},
        {"key1": 11},
        {"key1": 10}
    ]
    
    # We need to pass adjacency matrices to compute_motif_z_scores?
    # The function signature is compute_motif_z_scores(observed_counts, null_models, iterations)
    # But it calls count_motifs on null_models.
    # So we need to pass actual adjacency matrices, not counts.
    # Let's create dummy matrices that produce the counts we want?
    # That's hard.
    # Let's adjust the test to use the function as designed.
    # We will create a few simple graphs that have a specific motif count.
    
    # Graph 1: Triangle (1 count)
    g1 = np.array([[0,1,0],[0,0,1],[1,0,0]])
    # Graph 2: Triangle
    g2 = np.array([[0,1,0],[0,0,1],[1,0,0]])
    # Graph 3: Triangle
    g3 = np.array([[0,1,0],[0,0,1],[1,0,0]])
    
    # Observed: 10 triangles? No, we need a graph with 10 triangles.
    # Let's just test the math with mocked counts if we refactor?
    # No, we must test the real function.
    # Let's create a graph with 10 triangles?
    # A complete graph K4 has 4 triangles? No, 4 choose 3 = 4.
    # K5 has 10 triangles.
    adj_obs = np.ones((5,5)) - np.eye(5)
    observed_counts = count_motifs(adj_obs)
    # K5 has 10 directed triangles?
    # In a complete directed graph (no self loops), every 3 nodes form a tournament.
    # There are 2 types of tournaments on 3 nodes: transitive and cyclic.
    # A complete graph has all edges.
    # Number of 3-node subgraphs in K5 is 10.
    # Each subgraph is a complete directed graph (3 edges in each direction? No, 1 edge per pair).
    # Wait, our adj_obs is 1 for all i!=j.
    # So every 3 nodes form a "complete" subgraph (3 edges, 3 reverse edges? No, 6 edges).
    # Actually, our count_motifs counts induced subgraphs.
    # In K5, every 3 nodes have 6 edges (complete bidirectional).
    # So all 10 subgraphs are the same type.
    # observed_counts will have 1 entry with value 10.
    
    null_models = [g1, g2, g3]
    # Each g has 1 triangle.
    
    z_scores = compute_motif_z_scores(observed_counts, null_models, iterations=3)
    
    # Mean null = 1.0, Std null = 0.0 (all 1s)
    # Observed = 10.
    # Z = (10 - 1) / 0 -> inf
    # Let's check if it handles inf
    assert len(z_scores) == 1
    # The value should be inf or a very large number if we handled it.
    # Our implementation returns float('inf').
    assert z_scores[list(z_scores.keys())[0]] == float('inf')

def test_generate_null_model_empty():
    """Test null model generation on empty graph."""
    adj = np.zeros((3, 3))
    nulls = generate_null_model(adj, iterations=5)
    assert len(nulls) == 5
    for n in nulls:
        assert np.sum(n) == 0

def test_generate_null_model_single_edge():
    """Test null model generation on graph with 1 edge."""
    adj = np.zeros((3, 3))
    adj[0, 1] = 1
    nulls = generate_null_model(adj, iterations=5)
    # With 1 edge, we cannot rewire (need 2 edges).
    # So all nulls should be the same as original.
    for n in nulls:
        assert np.array_equal(n, adj)