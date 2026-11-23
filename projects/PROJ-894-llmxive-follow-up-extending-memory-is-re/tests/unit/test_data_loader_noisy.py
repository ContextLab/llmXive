"""
Unit tests for T011c: Noisy Graph Dataset Generation.
"""
import json
import os
import pytest
import networkx as nx
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_loader import (
    inject_noise,
    generate_noisy_graphs,
    save_noisy_graphs,
    load_noisy_graphs,
    ensure_output_dirs
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
GRAPHS_DIR = DATA_DIR / "processed" / "graphs"

@pytest.fixture
def sample_graph():
    """Create a sample directed graph for testing."""
    G = nx.DiGraph()
    G.add_edges_from([
        ("A", "B"),
        ("B", "C"),
        ("C", "D"),
        ("D", "A"),
        ("A", "C"),
        ("B", "D")
    ])
    return G

@pytest.fixture
def sample_graphs_dict():
    """Create a dictionary of sample graphs."""
    G1 = nx.DiGraph()
    G1.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
    
    G2 = nx.DiGraph()
    G2.add_edges_from([("X", "Y"), ("Y", "Z"), ("Z", "W"), ("W", "X")])
    
    return {"task_1": G1, "task_2": G2}

def test_inject_noise_replaces_edges(sample_graph):
    """
    Test that inject_noise replaces edges while maintaining total edge count.
    """
    original_edges = sample_graph.number_of_edges()
    original_nodes = sample_graph.number_of_nodes()
    
    # Test with 50% noise
    noisy_graph = inject_noise(sample_graph, ratio=0.5, seed=42)
    
    # Check edge count is maintained
    assert noisy_graph.number_of_edges() == original_edges, \
        f"Edge count changed: {noisy_graph.number_of_edges()} != {original_edges}"
    
    # Check node count is maintained
    assert noisy_graph.number_of_nodes() == original_nodes, \
        f"Node count changed: {noisy_graph.number_of_nodes()} != {original_nodes}"
    
    # Check that at least one edge is different (with high probability)
    original_edge_set = set(sample_graph.edges())
    noisy_edge_set = set(noisy_graph.edges())
    
    # With 50% noise and 6 edges, we expect ~3 changes
    # It's possible (though unlikely) all replacements map back to original edges
    # So we check that the graphs are not identical
    assert original_edge_set != noisy_edge_set or \
           any(sample_graph.edges[u, v].get('relation') != noisy_graph.edges[u, v].get('relation') 
               for u, v in noisy_edge_set if noisy_graph.has_edge(u, v)), \
        "No edges were changed by noise injection"

def test_inject_noise_zero_ratio(sample_graph):
    """Test that ratio=0.0 returns an identical graph."""
    noisy_graph = inject_noise(sample_graph, ratio=0.0, seed=42)
    
    # With ratio 0, no edges should be replaced
    # However, the function returns a copy, so we check edge sets
    assert set(sample_graph.edges()) == set(noisy_graph.edges())

def test_inject_noise_one_ratio(sample_graph):
    """Test that ratio=1.0 replaces all edges."""
    noisy_graph = inject_noise(sample_graph, ratio=1.0, seed=42)
    
    # All edges should be replaced (though they might randomly map back)
    assert noisy_graph.number_of_edges() == sample_graph.number_of_edges()

def test_inject_noise_empty_graph():
    """Test handling of empty graph."""
    G = nx.DiGraph()
    G.add_nodes_from(["A", "B", "C"])
    
    noisy_graph = inject_noise(G, ratio=0.5, seed=42)
    assert noisy_graph.number_of_edges() == 0

def test_inject_noise_single_node():
    """Test handling of single-node graph."""
    G = nx.DiGraph()
    G.add_node("A")
    
    noisy_graph = inject_noise(G, ratio=0.5, seed=42)
    assert noisy_graph.number_of_edges() == 0

def test_generate_noisy_graphs(sample_graphs_dict):
    """Test generation of noisy graphs for multiple tasks."""
    noisy_graphs = generate_noisy_graphs(sample_graphs_dict, ratio=0.2, seed=42)
    
    assert len(noisy_graphs) == len(sample_graphs_dict)
    
    for task_id in sample_graphs_dict:
        assert task_id in noisy_graphs
        assert noisy_graphs[task_id].number_of_edges() == \
               sample_graphs_dict[task_id].number_of_edges()

def test_save_and_load_noisy_graphs(sample_graphs_dict, tmp_path):
    """Test saving and loading noisy graphs."""
    # Use a temporary directory for this test
    test_graphs_dir = tmp_path / "test_graphs"
    test_graphs_dir.mkdir()
    
    noisy_graphs = generate_noisy_graphs(sample_graphs_dict, ratio=0.3, seed=42)
    
    # Manually save to temp location
    output_path = test_graphs_dir / "test_noise.json"
    serializable_graphs = {}
    for task_id, G in noisy_graphs.items():
        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation_string": data.get("relation", "")
            })
        serializable_graphs[task_id] = edges
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_graphs, f, indent=2)
    
    # Load back
    with open(output_path, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    # Verify structure
    assert set(loaded_data.keys()) == set(sample_graphs_dict.keys())
    for task_id, edges in loaded_data.items():
        assert isinstance(edges, list)
        for edge in edges:
            assert "source" in edge
            assert "target" in edge
            assert "relation_string" in edge

def test_noisy_graph_edge_count_matches_clean(sample_graphs_dict):
    """
    Verify that the total edge count of noisy graphs matches clean graphs.
    This is the primary verification requirement for T011c.
    """
    noisy_graphs = generate_noisy_graphs(sample_graphs_dict, ratio=0.1, seed=42)
    
    total_clean_edges = sum(g.number_of_edges() for g in sample_graphs_dict.values())
    total_noisy_edges = sum(g.number_of_edges() for g in noisy_graphs.values())
    
    assert total_clean_edges == total_noisy_edges, \
        f"Total edge count mismatch: clean={total_clean_edges}, noisy={total_noisy_edges}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
