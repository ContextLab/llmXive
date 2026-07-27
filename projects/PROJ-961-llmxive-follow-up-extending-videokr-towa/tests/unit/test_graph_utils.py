"""
Unit tests for graph_utils.py shortest path logic.
"""
import unittest
import sys
from collections import deque

sys.path.insert(0, 'code')

from utils.graph_utils import (
    build_undirected_graph,
    build_directed_graph,
    shortest_path_bfs,
    calculate_hop_distance,
    get_connected_components,
    get_hop_distribution
)


class TestGraphUtils(unittest.TestCase):
    """Tests for graph utility functions."""

    def test_build_undirected_graph(self):
        """Test building an undirected graph from edge list."""
        edges = [
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('A', 'D')
        ]
        graph = build_undirected_graph(edges)
        
        # Check neighbors
        self.assertIn('B', graph['A'])
        self.assertIn('D', graph['A'])
        self.assertIn('A', graph['B']) # Undirected
        self.assertIn('C', graph['B'])

    def test_build_directed_graph(self):
        """Test building a directed graph from edge list."""
        edges = [
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D')
        ]
        graph = build_directed_graph(edges)
        
        self.assertIn('B', graph['A'])
        self.assertNotIn('A', graph['B']) # Directed

    def test_shortest_path_bfs_connected(self):
        """Test BFS shortest path in a connected graph."""
        edges = [
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('A', 'E'),
            ('E', 'D')
        ]
        graph = build_undirected_graph(edges)
        
        # Shortest path from A to D: A->E->D (2 hops) or A->B->C->D (3 hops)
        # BFS should find the shortest one
        path = shortest_path_bfs(graph, 'A', 'D')
        
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 3) # A, E, D
        self.assertEqual(path[0], 'A')
        self.assertEqual(path[-1], 'D')

    def test_shortest_path_bfs_disconnected(self):
        """Test BFS shortest path when nodes are disconnected."""
        edges = [
            ('A', 'B'),
            ('C', 'D')
        ]
        graph = build_undirected_graph(edges)
        
        path = shortest_path_bfs(graph, 'A', 'D')
        
        self.assertIsNone(path)

    def test_shortest_path_bfs_same_node(self):
        """Test BFS shortest path from node to itself."""
        edges = [('A', 'B')]
        graph = build_undirected_graph(edges)
        
        path = shortest_path_bfs(graph, 'A', 'A')
        
        self.assertEqual(path, ['A'])

    def test_calculate_hop_distance(self):
        """Test hop distance calculation."""
        edges = [
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D')
        ]
        graph = build_undirected_graph(edges)
        
        dist = calculate_hop_distance(graph, 'A', 'D')
        self.assertEqual(dist, 3) # A-B-C-D

        dist = calculate_hop_distance(graph, 'A', 'B')
        self.assertEqual(dist, 1)

        dist = calculate_hop_distance(graph, 'A', 'Z') # Z not in graph
        self.assertEqual(dist, -1)

    def test_get_connected_components(self):
        """Test finding connected components."""
        edges = [
            ('A', 'B'),
            ('B', 'C'),
            ('D', 'E')
        ]
        graph = build_undirected_graph(edges)
        
        components = get_connected_components(graph)
        
        self.assertEqual(len(components), 2)
        # Check sets
        comp_sets = [set(c) for c in components]
        self.assertIn({'A', 'B', 'C'}, comp_sets)
        self.assertIn({'D', 'E'}, comp_sets)

    def test_get_hop_distribution(self):
        """Test hop distribution calculation."""
        edges = [
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('D', 'E')
        ]
        graph = build_undirected_graph(edges)
        
        # Distribution of shortest paths from 'A'
        dist = get_hop_distribution(graph, 'A')
        
        self.assertIn(0, dist) # A to A
        self.assertIn(1, dist) # A to B
        self.assertIn(2, dist) # A to C
        self.assertIn(3, dist) # A to D
        self.assertIn(4, dist) # A to E
        
        # Check counts
        self.assertEqual(dist[1], 1)
        self.assertEqual(dist[2], 1)


if __name__ == '__main__':
    unittest.main()