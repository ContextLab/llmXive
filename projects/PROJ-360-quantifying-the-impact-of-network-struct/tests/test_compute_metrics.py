import os
import json
import pickle
import tempfile
import unittest
from pathlib import Path
import networkx as nx
import pandas as pd

# Import the module under test
import sys
sys.path.insert(0, 'code')
from compute_metrics import (
    load_graphs_from_directory,
    compute_lcc_metrics,
    compute_metrics_for_graph,
    save_metrics_to_csv,
    compute_physical_descriptors
)

class TestComputeMetrics(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.network_dir = os.path.join(self.temp_dir, "networks")
        os.makedirs(self.network_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_graphs_from_directory(self):
        # Create a dummy graph
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])
        G.graph['material_id'] = 'mp-123'
        
        pkl_path = os.path.join(self.network_dir, "mp-123.pkl")
        with open(pkl_path, 'wb') as f:
            pickle.dump(G, f)

        graphs = load_graphs_from_directory(self.network_dir)
        self.assertIn('mp-123', graphs)
        self.assertEqual(graphs['mp-123'].number_of_nodes(), 3)

    def test_compute_lcc_metrics(self):
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 4)]) # Line graph
        
        avg_path, clustering = compute_lcc_metrics(G)
        
        # Line graph 1-2-3-4: avg path should be > 1, clustering 0
        self.assertGreater(avg_path, 1.0)
        self.assertEqual(clustering, 0.0)

    def test_compute_metrics_for_graph(self):
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])
        
        # Dummy manifest
        manifest = {
            "materials": {
                "mp-123": {
                    "k_x": 10.0, "k_y": 10.0, "k_z": 10.0
                }
            }
        }
        
        metrics = compute_metrics_for_graph("mp-123", G, None, manifest)
        
        self.assertEqual(metrics['material_id'], 'mp-123')
        self.assertIn('average_degree', metrics)
        self.assertIn('thermal_conductivity_scalar', metrics)
        self.assertEqual(metrics['thermal_conductivity_scalar'], 10.0)

    def test_save_metrics_to_csv(self):
        metrics_list = [
            {
                "material_id": "mp-1",
                "average_degree": 2.0,
                "average_path_length": 1.5,
                "clustering_coefficient": 0.1,
                "unit_cell_volume": 100.0,
                "total_atom_count": 10,
                "mean_atomic_mass": 25.0,
                "thermal_conductivity_scalar": 5.0
            }
        ]
        output_path = os.path.join(self.temp_dir, "metrics.csv")
        save_metrics_to_csv(metrics_list, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        df = pd.read_csv(output_path)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['material_id'], 'mp-1')

if __name__ == '__main__':
    unittest.main()