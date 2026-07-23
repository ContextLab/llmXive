"""
Unit tests for graph rewiring functionality (Maslov-Sneppen algorithm).
"""
import pytest
import networkx as nx
from pathlib import Path
import tempfile
import shutil

from network_analysis import (
    maslov_sneppen_rewire,
    generate_rewired_graphs,
    NetworkAnalysisError
)


def test_maslov_sneppen_preserves_degree_sequence():
    """Test that Maslov-Sneppen rewire preserves the degree sequence."""
    # Create a simple graph with known degrees
    G = nx.Graph()
    G.add_edges_from([
        (1, 2), (1, 3), (1, 4),
        (2, 3), (2, 5),
        (3, 4), (3, 5),
        (4, 5), (4, 6),
        (5, 6)
    ])
    
    original_degrees = sorted([d for n, d in G.degree()])
    
    # Rewire
    G_rewired = maslov_sneppen_rewire(G, n_swaps=100)
    
    rewired_degrees = sorted([d for n, d in G_rewired.degree()])
    
    assert original_degrees == rewired_degrees, "Degree sequence must be preserved"
    assert G.number_of_nodes() == G_rewired.number_of_nodes()
    assert G.number_of_edges() == G_rewired.number_of_edges()


def test_maslov_sneppen_changes_topology():
    """Test that rewiring actually changes the graph structure (unless graph is trivial)."""
    # Create a graph that is likely to change
    G = nx.erdos_renyi_graph(20, 0.3, seed=42)
    
    original_edges = set(G.edges())
    
    G_rewired = maslov_sneppen_rewire(G, n_swaps=500)
    
    rewired_edges = set(G_rewired.edges())
    
    # They should not be identical (high probability for non-trivial graphs)
    # Note: It is theoretically possible for them to be identical if swaps fail to find valid pairs,
    # but with 500 swaps on 20 nodes, it's extremely unlikely.
    if G.number_of_edges() > 2:
        assert original_edges != rewired_edges, "Rewired graph should have different topology"


def test_generate_rewired_graphs_saves_files():
    """Test that generate_rewired_graphs saves files to the specified directory."""
    G = nx.erdos_renyi_graph(15, 0.2, seed=123)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        n_graphs = 5
        
        paths = generate_rewired_graphs(G, n_graphs=n_graphs, n_swaps_per_graph=100, output_dir=output_dir)
        
        assert len(paths) == n_graphs
        for p in paths:
            assert p.exists()
            assert p.suffix == ".graphml"
            # Verify it can be read back
            G_loaded = nx.read_graphml(p)
            assert G_loaded.number_of_nodes() == G.number_of_nodes()
            assert G_loaded.number_of_edges() == G.number_of_edges()


def test_rewire_small_graph():
    """Test rewiring on a very small graph."""
    G = nx.path_graph(4)
    G_rewired = maslov_sneppen_rewire(G, n_swaps=10)
    
    # Path graph has degrees [1, 2, 2, 1]. Rewired should have same.
    original_degrees = sorted([d for n, d in G.degree()])
    rewired_degrees = sorted([d for n, d in G_rewired.degree()])
    assert original_degrees == rewired_degrees


def test_rewire_disconnected_graph():
    """Test rewiring on a disconnected graph."""
    G = nx.Graph()
    G.add_edges_from([(1, 2), (3, 4)])
    
    G_rewired = maslov_sneppen_rewire(G, n_swaps=10)
    
    # Degrees must be preserved: [1, 1, 1, 1]
    original_degrees = sorted([d for n, d in G.degree()])
    rewired_degrees = sorted([d for n, d in G_rewired.degree()])
    assert original_degrees == rewired_degrees
    # Number of connected components might change, but degrees must stay same.
    # However, double_edge_swap might merge components if it swaps edges between them?
    # Actually, double_edge_swap preserves degrees, so if you have two disjoint edges (1-2, 3-4),
    # you can swap to (1-3, 2-4) which connects them, or (1-4, 2-3).
    # So connectivity is not preserved, but degrees are.
    assert G_rewired.number_of_nodes() == G.number_of_nodes()
    assert G_rewired.number_of_edges() == G.number_of_edges()
