"""
Unit tests for graph construction and manipulation utilities.
"""
import pytest
import networkx as nx
from graph_utils import build_memory_graph, inject_noise, validate_graph, get_graph_statistics

def test_build_memory_graph_from_dict(sample_graph_data):
    """Test building a NetworkX graph from a dictionary structure."""
    G = build_memory_graph(sample_graph_data)
    assert isinstance(G, nx.Graph)
    assert G.number_of_nodes() == 3
    assert G.number_of_edges() == 2
    assert "Alice" in [G.nodes[n]["content"] for n in G.nodes() if "content" in G.nodes[n]]

def test_inject_noise_preserves_structure(sample_graph_data):
    """Test that noise injection adds edges but keeps original nodes."""
    G = build_memory_graph(sample_graph_data)
    original_edges = G.number_of_edges()
    noisy_G = inject_noise(G, noise_rate=0.5, seed=42)
    assert noisy_G.number_of_nodes() == G.number_of_nodes()
    assert noisy_G.number_of_edges() >= original_edges

def test_validate_graph_returns_true_for_valid_graph(sample_graph_data):
    """Test validation on a correctly formed graph."""
    G = build_memory_graph(sample_graph_data)
    assert validate_graph(G) is True

def test_get_graph_statistics(sample_graph_data):
    """Test calculation of basic graph statistics."""
    G = build_memory_graph(sample_graph_data)
    stats = get_graph_statistics(G)
    assert "num_nodes" in stats
    assert "num_edges" in stats
    assert stats["num_nodes"] == 3
    assert stats["num_edges"] == 2
