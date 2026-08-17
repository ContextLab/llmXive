import unittest
import networkx as nx
import numpy as np
from code.generate_networks import generate_random_graph, generate_scale_free_graph, compute_metrics_for_graph

class TestGraphGeneration(unittest.TestCase):

    def test_generate_random_graphs(self):
        num_graphs = 10
        n = 100
        graphs = [generate_random_graph(n, i) for i in range(num_graphs)]
        for graph in graphs:
            self.assertEqual(graph.number_of_nodes(), n)
            self.assertEqual(graph.name, "random")

    def test_generate_scale_free_graphs(self):
        num_graphs = 10
        n = 100
        graphs = [generate_scale_free_graph(n, i) for i in range(num_graphs)]
        for graph in graphs:
            self.assertEqual(graph.number_of_nodes(), n)
            self.assertEqual(graph.name, "scale_free")

    def test_compute_metrics_validity(self):
      graph = nx.erdos_renyi_graph(100, 0.1)
      metrics = compute_metrics_for_graph(graph)
      self.assertTrue(0 <= metrics["clustering_coefficient"] <= 1)
      self.assertIsInstance(metrics["average_path_length"], float)

if __name__ == '__main__':
    unittest.main()