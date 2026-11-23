"""
Unit tests for traversal strategies.
Specifically tests the Full traversal logic on a synthetic small graph.
"""
import pytest
import networkx as nx
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from strategies.full import FullTraversal

@pytest.fixture
def simple_graph():
    """Create a simple directed graph for testing."""
    G = nx.DiGraph()
    # Create a small chain: A -> B -> C
    G.add_edge("A", "B")
    G.add_edge("B", "C")
    # Add a branch: A -> D
    G.add_edge("A", "D")
    
    # Add attributes
    for node in G.nodes():
        G.nodes[node]["valid"] = True
        G.nodes[node]["content"] = f"Content {node}"
        
    return G

@pytest.fixture
def disconnected_graph():
    """Create a graph with a disconnected component."""
    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("C", "D") # Disconnected from A
    
    for node in G.nodes():
        G.nodes[node]["valid"] = True
        
    return G

def test_full_traversal_basic(simple_graph):
    """Test that FullTraversal visits all reachable nodes."""
    strategy = FullTraversal()
    success, path, stats = strategy.traverse(simple_graph, "A")
    
    assert success is True
    assert "A" in path
    assert "B" in path
    assert "C" in path
    assert "D" in path
    assert stats["nodes_visited"] == 4
    # Check path contains all nodes (order might vary slightly if graph structure changes, 
    # but BFS on this specific graph is deterministic: A, B, D, C or A, D, B, C depending on edge order)
    assert len(path) == 4

def test_full_traversal_disconnected(disconnected_graph):
    """Test that FullTraversal only visits reachable nodes from start."""
    strategy = FullTraversal()
    success, path, stats = strategy.traverse(disconnected_graph, "A")
    
    assert success is True
    assert "A" in path
    assert "B" in path
    assert "C" not in path # C is not reachable from A
    assert "D" not in path
    assert stats["nodes_visited"] == 2

def test_full_traversal_invalid_start(simple_graph):
    """Test that FullTraversal handles invalid start node."""
    strategy = FullTraversal()
    success, path, stats = strategy.traverse(simple_graph, "Z")
    
    assert success is False
    assert path == []
    assert stats["nodes_visited"] == 0

def test_full_traversal_no_edges():
    """Test traversal on a single node graph."""
    G = nx.DiGraph()
    G.add_node("Single")
    G.nodes["Single"]["valid"] = True
    
    strategy = FullTraversal()
    success, path, stats = strategy.traverse(G, "Single")
    
    assert success is True
    assert path == ["Single"]
    assert stats["nodes_visited"] == 1
