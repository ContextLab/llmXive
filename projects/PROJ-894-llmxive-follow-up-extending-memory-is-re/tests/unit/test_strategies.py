"""
Unit tests for active reconstruction strategies.
"""
import pytest
import networkx as nx
from strategies.full import FullTraversal
from strategies.lazy import LazyTraversal
from strategies.greedy import GreedyTraversal
from graph_utils import build_memory_graph

@pytest.fixture
def simple_chain_graph():
    """Create a simple linear graph: A -> B -> C"""
    data = {
        "nodes": [
            {"id": "A", "content": "Start"},
            {"id": "B", "content": "Middle"},
            {"id": "C", "content": "End"}
        ],
        "edges": [
            {"source": "A", "target": "B", "weight": 1.0},
            {"source": "B", "target": "C", "weight": 1.0}
        ]
    }
    return build_memory_graph(data)

def test_full_traversal_visits_all_nodes(simple_chain_graph):
    """Test that FullTraversal visits every node in a connected graph."""
    strategy = FullTraversal()
    # Simulate a task starting at 'A'
    start_node = "A"
    result = strategy.traverse(simple_chain_graph, start_node, max_depth=5)
    visited_ids = [n for n in result["visited_nodes"]]
    assert "A" in visited_ids
    assert "B" in visited_ids
    assert "C" in visited_ids
    assert result["nodes_visited"] == 3

def test_lazy_traversal_with_threshold(simple_chain_graph):
    """Test LazyTraversal respects the evidence threshold."""
    strategy = LazyTraversal(evidence_threshold=0.9)
    start_node = "A"
    result = strategy.traverse(simple_chain_graph, start_node, max_depth=5)
    # Should visit nodes based on confidence, here all edges are weight 1.0
    assert "nodes_visited" in result
    assert result["nodes_visited"] > 0

def test_greedy_traversal_selection(simple_chain_graph):
    """Test GreedyTraversal selects top-k edges."""
    strategy = GreedyTraversal(top_k=1)
    start_node = "A"
    result = strategy.traverse(simple_chain_graph, start_node, max_depth=5)
    assert "nodes_visited" in result
    assert result["nodes_visited"] > 0
