"""
Unit tests for graph_utils.py
"""
import pytest
import json
import os
from pathlib import Path
import networkx as nx
import numpy as np

# Import the module under test
from graph_utils import inject_noise, build_memory_graph, validate_graph, get_graph_statistics

# Fixtures
@pytest.fixture
def simple_graph():
    """Returns a simple graph with known structure."""
    return {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            {"source": "A", "target": "B", "relation": "rel1"},
            {"source": "B", "target": "C", "relation": "rel2"},
            {"source": "C", "target": "D", "relation": "rel3"},
            {"source": "A", "target": "C", "relation": "rel4"}
        ]
    }

@pytest.fixture
def single_node_graph():
    """Returns a graph with a single node and no edges."""
    return {
        "nodes": ["A"],
        "edges": []
    }

@pytest.fixture
def empty_graph():
    """Returns an empty graph."""
    return {
        "nodes": [],
        "edges": []
    }

def test_inject_noise_replaces_edges(simple_graph):
    """
    Test that inject_noise replaces edges rather than adding them.
    The total edge count must remain constant.
    """
    original_edges = simple_graph["edges"]
    original_count = len(original_edges)
    original_edges_set = {(e["source"], e["target"]) for e in original_edges}
    
    # Inject noise with 50% ratio
    noisy_graph = inject_noise(simple_graph, ratio=0.5, seed=42)
    
    noisy_edges = noisy_graph["edges"]
    noisy_count = len(noisy_edges)
    
    # Assert edge count is preserved
    assert noisy_count == original_count, f"Edge count changed from {original_count} to {noisy_count}"
    
    # Assert that at least one edge was replaced (with high probability for 50% ratio)
    # We check if the set of edges is different
    noisy_edges_set = {(e["source"], e["target"]) for e in noisy_edges}
    
    # It's possible (though unlikely with 50% ratio) that the random selection
    # results in the same edges if we are unlucky, but with a fixed seed we expect change.
    # A robust check: if the graph is not a cycle that maps to itself, edges should change.
    # For this simple graph, 50% noise should definitely change something.
    # We assert that the sets are not identical to ensure noise was applied.
    # If they are identical, it means the random selection picked edges that, when replaced,
    # resulted in the same set (very unlikely for this specific graph and seed).
    # We rely on the seed 42 to produce a deterministic change.
    assert noisy_edges_set != original_edges_set, "Noise injection did not change any edges."

def test_inject_noise_no_self_loops(simple_graph):
    """Test that inject_noise does not create self-loops."""
    noisy_graph = inject_noise(simple_graph, ratio=1.0, seed=42)
    for edge in noisy_graph["edges"]:
        assert edge["source"] != edge["target"], f"Self-loop detected: {edge}"

def test_inject_noise_preserves_nodes(simple_graph):
    """Test that inject_noise preserves the set of nodes."""
    noisy_graph = inject_noise(simple_graph, ratio=0.5, seed=42)
    original_nodes = set(simple_graph["nodes"])
    noisy_nodes = set(noisy_graph["nodes"])
    assert original_nodes == noisy_nodes, "Node set changed during noise injection"

def test_degenerate_graph_handling(single_node_graph):
    """Test handling of a single-node graph."""
    # Should not crash
    result = inject_noise(single_node_graph, ratio=0.1, seed=42)
    assert result["edges"] == []
    assert result["nodes"] == ["A"]

def test_empty_graph_handling(empty_graph):
    """Test handling of an empty graph."""
    result = inject_noise(empty_graph, ratio=0.1, seed=42)
    assert result["edges"] == []
    assert result["nodes"] == []

def test_validate_graph_valid(simple_graph):
    """Test validation of a valid graph."""
    is_valid, message = validate_graph(simple_graph)
    assert is_valid
    assert message == "Graph is valid"

def test_validate_graph_invalid_structure():
    """Test validation of a graph with invalid structure."""
    invalid_graph = {
        "nodes": ["A"],
        "edges": [{"source": "A"}] # Missing target
    }
    is_valid, message = validate_graph(invalid_graph)
    assert not is_valid
    assert "missing" in message.lower()

def test_get_graph_statistics(simple_graph):
    """Test graph statistics calculation."""
    stats = get_graph_statistics(simple_graph)
    assert stats["num_nodes"] == 4
    assert stats["num_edges"] == 4
    assert stats["density"] > 0
    assert stats["average_degree"] > 0

def test_build_memory_graph():
    """Test building a memory graph from triples."""
    triples = [("A", "is", "B"), ("B", "has", "C")]
    graph = build_memory_graph(triples)
    assert len(graph["nodes"]) == 3
    assert len(graph["edges"]) == 2
    assert "A" in graph["nodes"]
    assert "B" in graph["nodes"]
    assert "C" in graph["nodes"]

def test_graph_noise_42_determinism(simple_graph):
    """Test that noise injection with seed 42 is deterministic."""
    graph1 = inject_noise(simple_graph, ratio=0.5, seed=42)
    graph2 = inject_noise(simple_graph, ratio=0.5, seed=42)
    
    assert json.dumps(graph1, sort_keys=True) == json.dumps(graph2, sort_keys=True)
