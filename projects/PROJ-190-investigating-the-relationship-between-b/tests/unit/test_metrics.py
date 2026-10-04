import unittest
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.graph.metrics import calculate_global_efficiency

class TestGlobalEfficiency(unittest.TestCase):

    def test_complete_graph(self):
        """
        For a complete graph of N nodes, the shortest path between any two nodes is 1.
        Global Efficiency should be 1.0.
        """
        n = 5
        adj = np.ones((n, n)) - np.eye(n)  # Complete graph, no self loops
        eff = calculate_global_efficiency(adj)
        self.assertAlmostEqual(eff, 1.0, places=5)

    def test_disconnected_graph(self):
        """
        If the graph is disconnected (two components with no path between them),
        the shortest path is infinity, so 1/d is 0.
        Global efficiency should be lower than a connected graph.
        """
        # Two separate triangles (n=3 each)
        n = 6
        adj = np.zeros((n, n))
        # Component 1: nodes 0,1,2
        adj[0, 1] = adj[1, 0] = 1
        adj[1, 2] = adj[2, 1] = 1
        adj[0, 2] = adj[2, 0] = 1
        # Component 2: nodes 3,4,5
        adj[3, 4] = adj[4, 3] = 1
        adj[4, 5] = adj[5, 4] = 1
        adj[3, 5] = adj[5, 3] = 1
        
        eff = calculate_global_efficiency(adj)
        # Max possible efficiency for disconnected graph is less than 1.0
        # Specifically, only intra-component paths contribute.
        # For each component of 3 nodes: 3 pairs with dist 1. Total 6 pairs with dist 1.
        # Total pairs = 6*5 = 30.
        # Sum inv_dist = 6.
        # Eff = 6 / 30 = 0.2
        self.assertAlmostEqual(eff, 0.2, places=5)

    def test_single_edge(self):
        """
        A simple path graph of 3 nodes: 0-1-2.
        Paths: (0,1)=1, (1,2)=1, (0,2)=2.
        Inverse: 1, 1, 0.5. Sum = 2.5.
        Pairs = 3*2 = 6.
        Eff = 2.5 / 6 = 0.41666...
        """
        adj = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        eff = calculate_global_efficiency(adj)
        expected = 2.5 / 6.0
        self.assertAlmostEqual(eff, expected, places=5)

    def test_empty_graph(self):
        """
        Graph with no edges should have efficiency 0.0.
        """
        n = 3
        adj = np.zeros((n, n))
        eff = calculate_global_efficiency(adj)
        self.assertEqual(eff, 0.0)

    def test_single_node(self):
        """
        Graph with 1 node should have efficiency 0.0.
        """
        adj = np.array([[0]])
        eff = calculate_global_efficiency(adj)
        self.assertEqual(eff, 0.0)

    def test_weighted_graph(self):
        """
        Test with weighted edges. Shortest path should use weights.
        Nodes 0-1 (weight 1), 1-2 (weight 1), 0-2 (weight 10).
        Shortest path 0->2 is via 1 (1+1=2), not direct (10).
        Distances: (0,1)=1, (1,2)=1, (0,2)=2.
        Inverse: 1, 1, 0.5. Sum = 2.5.
        Pairs = 6. Eff = 0.41666...
        """
        adj = np.array([
            [0, 1, 10],
            [1, 0, 1],
            [10, 1, 0]
        ])
        eff = calculate_global_efficiency(adj)
        expected = 2.5 / 6.0
        self.assertAlmostEqual(eff, expected, places=5)

if __name__ == '__main__':
    unittest.main()