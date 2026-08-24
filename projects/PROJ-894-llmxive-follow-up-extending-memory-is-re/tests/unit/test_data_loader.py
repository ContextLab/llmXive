"""
Unit tests for data_loader.py
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import (
    inject_noise,
    build_memory_graph,
    extract_traces_from_context,
    generate_noisy_graphs,
    save_noisy_graphs,
    load_noisy_graphs,
    ensure_output_dirs
)

# Fixtures
@pytest.fixture
def sample_graph():
    """Returns a sample graph for testing."""
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
def sample_tasks():
    """Returns sample tasks for testing."""
    return [
        {
            "question": "What is the capital of France?",
            "context": "Paris is the capital of France. France is in Europe.",
            "answer": "Paris"
        },
        {
            "question": "Who wrote Hamlet?",
            "context": "William Shakespeare wrote Hamlet. Shakespeare was English.",
            "answer": "William Shakespeare"
        }
    ]

def test_inject_noise_replaces_edges(sample_graph):
    """
    Test that inject_noise replaces edges rather than adding them.
    The total edge count must remain constant.
    """
    original_edges = sample_graph["edges"]
    original_count = len(original_edges)
    original_edges_set = {(e["source"], e["target"]) for e in original_edges}
    
    # Inject noise with 50% ratio
    noisy_graph = inject_noise(sample_graph, ratio=0.5, seed=42)
    
    noisy_edges = noisy_graph["edges"]
    noisy_count = len(noisy_edges)
    
    # Assert edge count is preserved
    assert noisy_count == original_count, f"Edge count changed from {original_count} to {noisy_count}"
    
    # Assert that at least one edge was replaced (with high probability for 50% ratio)
    noisy_edges_set = {(e["source"], e["target"]) for e in noisy_edges}
    
    # With seed 42, we expect the edges to change
    assert noisy_edges_set != original_edges_set, "Noise injection did not change any edges."

def test_inject_noise_no_self_loops(sample_graph):
    """Test that inject_noise does not create self-loops."""
    noisy_graph = inject_noise(sample_graph, ratio=1.0, seed=42)
    for edge in noisy_graph["edges"]:
        assert edge["source"] != edge["target"], f"Self-loop detected: {edge}"

def test_inject_noise_preserves_nodes(sample_graph):
    """Test that inject_noise preserves the set of nodes."""
    noisy_graph = inject_noise(sample_graph, ratio=0.5, seed=42)
    original_nodes = set(sample_graph["nodes"])
    noisy_nodes = set(noisy_graph["nodes"])
    assert original_nodes == noisy_nodes, "Node set changed during noise injection"

def test_build_memory_graph():
    """Test building a memory graph from triples."""
    triples = [("A", "is", "B"), ("B", "has", "C")]
    graph = build_memory_graph(triples)
    assert len(graph["nodes"]) == 3
    assert len(graph["edges"]) == 2
    assert "A" in graph["nodes"]
    assert "B" in graph["nodes"]
    assert "C" in graph["nodes"]

def test_generate_noisy_graphs():
    """Test generating noisy graphs from a dictionary of clean graphs."""
    clean_graphs = {
        "task1": {
            "nodes": ["A", "B"],
            "edges": [{"source": "A", "target": "B", "relation": "rel"}]
        },
        "task2": {
            "nodes": ["X", "Y", "Z"],
            "edges": [
                {"source": "X", "target": "Y", "relation": "rel1"},
                {"source": "Y", "target": "Z", "relation": "rel2"}
            ]
        }
    }
    
    noisy_graphs = generate_noisy_graphs(clean_graphs, ratio=0.5, seed=42)
    
    assert len(noisy_graphs) == len(clean_graphs)
    assert "task1" in noisy_graphs
    assert "task2" in noisy_graphs
    
    # Check edge counts are preserved
    for task_id in clean_graphs:
        assert len(noisy_graphs[task_id]["edges"]) == len(clean_graphs[task_id]["edges"])

def test_save_and_load_noisy_graphs(tmp_path):
    """Test saving and loading noisy graphs."""
    noisy_graphs = {
        "task1": {
            "nodes": ["A", "B"],
            "edges": [{"source": "A", "target": "B", "relation": "rel"}]
        }
    }
    
    output_path = tmp_path / "test_graph_noise_42.json"
    
    # Save
    save_noisy_graphs(noisy_graphs, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Load
    loaded_graphs = load_noisy_graphs(output_path)
    
    assert loaded_graphs == noisy_graphs

def test_noisy_graph_edge_count_matches_clean(sample_graph):
    """Test that noisy graph has the same number of edges as clean graph."""
    noisy_graph = inject_noise(sample_graph, ratio=0.1, seed=42)
    assert len(noisy_graph["edges"]) == len(sample_graph["edges"])

def test_noisy_graph_determinism(sample_graph):
    """Test that noise injection with the same seed produces identical results."""
    graph1 = inject_noise(sample_graph, ratio=0.5, seed=42)
    graph2 = inject_noise(sample_graph, ratio=0.5, seed=42)
    
    assert json.dumps(graph1, sort_keys=True) == json.dumps(graph2, sort_keys=True)

def test_empty_graph_handling():
    """Test handling of an empty graph."""
    empty_graph = {"nodes": [], "edges": []}
    result = inject_noise(empty_graph, ratio=0.1, seed=42)
    assert result["edges"] == []
    assert result["nodes"] == []

def test_single_edge_graph():
    """Test handling of a graph with a single edge."""
    single_edge_graph = {
        "nodes": ["A", "B"],
        "edges": [{"source": "A", "target": "B", "relation": "rel"}]
    }
    result = inject_noise(single_edge_graph, ratio=1.0, seed=42)
    assert len(result["edges"]) == 1
    assert result["edges"][0]["source"] != result["edges"][0]["target"]  # No self-loop
