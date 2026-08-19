import unittest
import os
import csv
import json
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

    def test_full_generation_pipeline(self):
        """
        Integration test: assert data/raw/networks.csv exists and contains
        a representative set of network instances with correct columns.
        """
        output_path = "data/raw/networks.csv"
        
        # Check file existence
        self.assertTrue(os.path.exists(output_path), f"Output file {output_path} does not exist.")

        # Load and validate CSV
        with open(output_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Check row count (expecting >= 50 per task T012, min 10 per class)
        self.assertGreaterEqual(len(rows), 50, "CSV must contain at least 50 rows.")

        # Check required columns against schema (T006a)
        required_columns = {
            'id', 'class', 'N', 'clustering_coefficient', 'average_path_length',
            'average_degree', 'degree_distribution_stats'
        }
        actual_columns = set(rows[0].keys())
        self.assertTrue(required_columns.issubset(actual_columns), 
                        f"Missing columns: {required_columns - actual_columns}")

        # Check representation across classes
        classes_found = set(row['class'] for row in rows)
        expected_classes = {'random', 'scale_free', 'small_world', 'lattice', 'star'}
        self.assertTrue(expected_classes.issubset(classes_found), 
                        f"Missing classes: {expected_classes - classes_found}")

        # Validate metric bounds for a sample of rows
        for row in rows[:10]:
            # Clustering coefficient must be between 0 and 1
            cc = float(row['clustering_coefficient'])
            self.assertGreaterEqual(cc, 0.0)
            self.assertLessEqual(cc, 1.0)
            
            # Average path length must be positive and finite
            apl = float(row['average_path_length'])
            self.assertGreater(apl, 0.0)
            self.assertTrue(np.isfinite(apl))

        # Verify N consistency
        for row in rows:
            n_val = int(row['N'])
            self.assertGreaterEqual(n_val, 100)
            self.assertLessEqual(n_val, 200)

if __name__ == '__main__':
    unittest.main()
