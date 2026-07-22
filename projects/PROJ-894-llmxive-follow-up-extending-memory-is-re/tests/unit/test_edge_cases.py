"""
Unit tests for edge cases in graph traversal strategies.
Specifically tests zero edges and single node scenarios.
"""

import pytest
import networkx as nx
from typing import Dict, Any, List, Set, Optional, Tuple
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from strategies.full import FullTraversal
from strategies.lazy import LazyTraversal
from strategies.greedy import GreedyTraversal
from graph_utils import build_memory_graph, validate_graph


class TestZeroEdges:
    """Tests for graphs with zero edges."""

    def test_full_traversal_zero_edges(self):
        """Full traversal on a graph with nodes but no edges."""
        # Create a graph with 3 isolated nodes
        G = nx.Graph()
        G.add_nodes_from(['node_a', 'node_b', 'node_c'])
        
        # Validate graph
        assert validate_graph(G) is True
        
        # Initialize strategy
        strategy = FullTraversal()
        
        # Prepare task with zero-edge graph
        task = {
            'question': 'Test question',
            'context': 'Test context',
            'answer': 'Test answer',
            'graph': G,
            'start_node': 'node_a',
            'target_node': 'node_b'
        }
        
        # Execute traversal - should handle gracefully
        result = strategy.traverse(task)
        
        # Verify result structure
        assert 'success' in result
        assert 'nodes_visited' in result
        assert 'inference_time' in result
        
        # With zero edges, we can only visit the start node
        assert result['nodes_visited'] == 1
        # Should not fail, just return limited result
        assert result['success'] is False  # Cannot reach target without edges

    def test_lazy_traversal_zero_edges(self):
        """Lazy traversal on a graph with nodes but no edges."""
        G = nx.Graph()
        G.add_nodes_from(['node_x', 'node_y'])
        
        strategy = LazyTraversal(threshold=0.5)
        
        task = {
            'question': 'Test',
            'context': 'Test',
            'answer': 'Test',
            'graph': G,
            'start_node': 'node_x',
            'target_node': 'node_y'
        }
        
        result = strategy.traverse(task)
        
        assert result['nodes_visited'] == 1
        assert result['success'] is False

    def test_greedy_traversal_zero_edges(self):
        """Greedy traversal on a graph with nodes but no edges."""
        G = nx.Graph()
        G.add_nodes_from(['node_p', 'node_q'])
        
        strategy = GreedyTraversal(top_k=2)
        
        task = {
            'question': 'Test',
            'context': 'Test',
            'answer': 'Test',
            'graph': G,
            'start_node': 'node_p',
            'target_node': 'node_q'
        }
        
        result = strategy.traverse(task)
        
        assert result['nodes_visited'] == 1
        assert result['success'] is False


class TestSingleNode:
    """Tests for graphs with a single node."""

    def test_full_traversal_single_node(self):
        """Full traversal on a single-node graph."""
        G = nx.Graph()
        G.add_node('only_node')
        
        strategy = FullTraversal()
        
        task = {
            'question': 'Test',
            'context': 'Test',
            'answer': 'Test',
            'graph': G,
            'start_node': 'only_node',
            'target_node': 'only_node'
        }
        
        result = strategy.traverse(task)
        
        # Start and target are the same, so success should be True
        assert result['nodes_visited'] == 1
        assert result['success'] is True

    def test_lazy_traversal_single_node(self):
        """Lazy traversal on a single-node graph."""
        G = nx.Graph()
        G.add_node('single')
        
        strategy = LazyTraversal(threshold=0.5)
        
        task = {
            'question': 'Test',
            'context': 'Test',
            'answer': 'Test',
            'graph': G,
            'start_node': 'single',
            'target_node': 'single'
        }
        
        result = strategy.traverse(task)
        
        assert result['nodes_visited'] == 1
        assert result['success'] is True

    def test_greedy_traversal_single_node(self):
        """Greedy traversal on a single-node graph."""
        G = nx.Graph()
        G.add_node('lonely')
        
        strategy = GreedyTraversal(top_k=1)
        
        task = {
            'question': 'Test',
            'context': 'Test',
            'answer': 'Test',
            'graph': G,
            'start_node': 'lonely',
            'target_node': 'lonely'
        }
        
        result = strategy.traverse(task)
        
        assert result['nodes_visited'] == 1
        assert result['success'] is True

    def test_single_node_different_start_target(self):
        """Single node graph where start != target (impossible)."""
        G = nx.Graph()
        G.add_node('only_one')
        
        strategy = FullTraversal()
        
        task = {
            'question': 'Test',
            'context': 'Test',
            'answer': 'Test',
            'graph': G,
            'start_node': 'only_one',
            'target_node': 'nonexistent'
        }
        
        result = strategy.traverse(task)
        
        # Target doesn't exist in graph
        assert result['success'] is False
        assert result['nodes_visited'] == 1


class TestEmptyGraph:
    """Tests for completely empty graphs."""

    def test_full_traversal_empty_graph(self):
        """Full traversal on an empty graph."""
        G = nx.Graph()
        
        strategy = FullTraversal()
        
        task = {
            'question': 'Test',
            'context': 'Test',
            'answer': 'Test',
            'graph': G,
            'start_node': 'missing',
            'target_node': 'missing'
        }
        
        # Should handle gracefully without crashing
        with pytest.raises(Exception):
            # The strategy should raise an error for invalid graph state
            result = strategy.traverse(task)

    def test_validate_empty_graph(self):
        """Validate function should handle empty graphs."""
        G = nx.Graph()
        
        # Empty graph is technically valid but has no nodes
        # Our validation should handle this case
        is_valid = validate_graph(G)
        
        # Empty graph is valid structure, just empty
        assert is_valid is True