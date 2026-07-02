"""
Unit tests for network_analysis.py
"""

import unittest
import networkx as nx
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.network_analysis import (
    load_graph_from_adjacency_list,
    compute_degree_centrality,
    compute_eigenvector_centrality,
    compute_betweenness_centrality,
    compute_all_centrality_metrics,
    NetworkAnalysisError
)


class TestLoadGraph(unittest.TestCase):
    def test_load_undirected_graph(self):
        data = {
            'A': ['B', 'C'],
            'B': ['A'],
            'C': ['A']
        }
        G = load_graph_from_adjacency_list(data, directed=False)
        self.assertEqual(G.number_of_nodes(), 3)
        self.assertEqual(G.number_of_edges(), 2)
        self.assertTrue(G.has_edge('A', 'B'))
        self.assertTrue(G.has_edge('A', 'C'))

    def test_load_directed_graph(self):
        data = {
            'A': ['B'],
            'B': ['C'],
            'C': []
        }
        G = load_graph_from_adjacency_list(data, directed=True)
        self.assertEqual(G.number_of_nodes(), 3)
        self.assertEqual(G.number_of_edges(), 2)
        self.assertTrue(G.has_edge('A', 'B'))
        self.assertTrue(G.has_edge('B', 'C'))
        self.assertFalse(G.has_edge('B', 'A'))

    def test_empty_graph(self):
        data = {}
        G = load_graph_from_adjacency_list(data)
        self.assertEqual(G.number_of_nodes(), 0)


class TestDegreeCentrality(unittest.TestCase):
    def test_simple_graph(self):
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('A', 'C'), ('B', 'C')])
        result = compute_degree_centrality(G)
        # A: 2/2, B: 2/2, C: 2/2 -> 1.0 for all in a triangle
        # Wait, degree centrality is normalized by (n-1)
        # n=3, max degree=2.
        # A: 2/2 = 1.0
        # B: 2/2 = 1.0
        # C: 2/2 = 1.0
        self.assertAlmostEqual(result['A'], 1.0)
        self.assertAlmostEqual(result['B'], 1.0)
        self.assertAlmostEqual(result['C'], 1.0)

    def test_empty_graph(self):
        G = nx.Graph()
        result = compute_degree_centrality(G)
        self.assertEqual(result, {})


class TestEigenvectorCentrality(unittest.TestCase):
    def test_simple_graph(self):
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D')])
        # Path graph. Central nodes should have higher scores.
        result = compute_eigenvector_centrality(G)
        self.assertIn('A', result)
        self.assertIn('B', result)
        # B and C should be higher than A and D
        self.assertGreater(result['B'], result['A'])
        self.assertGreater(result['C'], result['D'])

    def test_disconnected_graph_fallback(self):
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('C', 'D')])
        # Eigenvector centrality on disconnected components can be tricky
        # Our implementation should handle it gracefully (return zeros or partial)
        result = compute_eigenvector_centrality(G)
        self.assertEqual(len(result), 4)
        # Should not crash, values might be zero or non-zero depending on implementation
        # The key is it doesn't raise an exception
        self.assertIsInstance(result, dict)


class TestBetweennessCentrality(unittest.TestCase):
    def test_simple_graph_exact(self):
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D')])
        # B and C are bridges
        result = compute_betweenness_centrality(G, k=0) # Force exact
        self.assertGreater(result['B'], 0)
        self.assertGreater(result['C'], 0)
        self.assertAlmostEqual(result['A'], 0.0)
        self.assertAlmostEqual(result['D'], 0.0)

    def test_simple_graph_sampling(self):
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D')])
        # With k > 0, it uses sampling
        result = compute_betweenness_centrality(G, k=10)
        # Should not crash, values might be approximate
        self.assertEqual(len(result), 4)
        self.assertIsInstance(result['B'], float)

    def test_large_graph_sampling_logic(self):
        # Create a graph with > 5000 nodes
        G = nx.barabasi_albert_graph(6000, 3)
        # This should trigger sampling logic in compute_betweenness_centrality
        # if k is not provided
        start_time = __import__('time').time()
        result = compute_betweenness_centrality(G) # No k provided
        elapsed = __import__('time').time() - start_time
        # Should be relatively fast (< 30 min, but for 6000 nodes it should be seconds/minutes)
        self.assertLess(elapsed, 1800) # Less than 30 minutes
        self.assertEqual(len(result), 6000)


class TestComputeAllCentralityMetrics(unittest.TestCase):
    def test_full_pipeline(self):
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E')])
        metrics = compute_all_centrality_metrics(G)
        
        self.assertIn('degree', metrics)
        self.assertIn('betweenness', metrics)
        self.assertIn('eigenvector', metrics)
        
        self.assertEqual(len(metrics['degree']), 5)
        self.assertEqual(len(metrics['betweenness']), 5)
        self.assertEqual(len(metrics['eigenvector']), 5)

    def test_empty_graph(self):
        G = nx.Graph()
        metrics = compute_all_centrality_metrics(G)
        self.assertEqual(metrics['degree'], {})
        self.assertEqual(metrics['betweenness'], {})
        self.assertEqual(metrics['eigenvector'], {})


if __name__ == '__main__':
    unittest.main()