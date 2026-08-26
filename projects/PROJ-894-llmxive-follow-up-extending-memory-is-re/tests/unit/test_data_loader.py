"""
Unit tests for data_loader.py - specifically for T011c noise injection.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import (
    inject_noise,
    save_noisy_graphs,
    ensure_output_dirs,
    fetch_locomo_dataset
)

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
    
    # Assert that at least one edge was replaced
    noisy_edges_set = {(e["source"], e["target"]) for e in noisy_edges}
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
    result = inject_noise(single_node_graph, ratio=0.1, seed=42)
    assert result["edges"] == []
    assert result["nodes"] == ["A"]

def test_empty_graph_handling(empty_graph):
    """Test handling of an empty graph."""
    result = inject_noise(empty_graph, ratio=0.1, seed=42)
    assert result["edges"] == []
    assert result["nodes"] == []

def test_graph_noise_42_determinism(simple_graph):
    """Test that noise injection with seed 42 is deterministic."""
    graph1 = inject_noise(simple_graph, ratio=0.5, seed=42)
    graph2 = inject_noise(simple_graph, ratio=0.5, seed=42)
    
    assert json.dumps(graph1, sort_keys=True) == json.dumps(graph2, sort_keys=True)

def test_save_noisy_graphs_creates_file(simple_graph):
    """Test that save_noisy_graphs creates the output file."""
    graphs = {"task1": simple_graph}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the GRAPHS_DIR
        import data_loader
        original_dir = data_loader.GRAPHS_DIR
        data_loader.GRAPHS_DIR = Path(tmpdir)
        
        try:
            output_path = save_noisy_graphs(graphs, "test_noise.json", seed=42)
            assert output_path.exists(), f"Output file not created at {output_path}"
            assert output_path.stat().st_size > 0, "Output file is empty"
            
            # Verify content
            with open(output_path, 'r') as f:
                saved_graphs = json.load(f)
            assert "task1" in saved_graphs
            assert len(saved_graphs["task1"]["edges"]) == len(simple_graph["edges"])
        finally:
            data_loader.GRAPHS_DIR = original_dir

def test_edge_replacement_logic(simple_graph):
    """
    Detailed test to verify that edges are actually being replaced.
    We check that the specific edges removed are not in the output,
    and that new edges exist.
    """
    original_edges = simple_graph["edges"]
    original_set = {(e["source"], e["target"]) for e in original_edges}
    
    # Use a high noise ratio to ensure changes
    noisy_graph = inject_noise(simple_graph, ratio=0.75, seed=123)
    noisy_set = {(e["source"], e["target"]) for e in noisy_graph["edges"]}
    
    # Count how many edges were replaced
    removed_count = len(original_set - noisy_set)
    added_count = len(noisy_set - original_set)
    
    # Both should be non-zero for a high noise ratio
    assert removed_count > 0, "No edges were removed"
    assert added_count > 0, "No new edges were added"
    assert removed_count == added_count, "Number of removed edges != number of added edges"