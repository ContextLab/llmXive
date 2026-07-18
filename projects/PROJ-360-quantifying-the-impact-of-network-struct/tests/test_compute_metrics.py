import os
import sys
import json
import pickle
import tempfile
import unittest
from pathlib import Path
import math

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'code'))

from compute_metrics import (
    load_graphs_from_directory, 
    load_thermal_conductivity_from_manifest,
    load_physical_descriptors_from_manifest,
    compute_metrics_for_graph,
    save_metrics_to_csv,
    main
)
import networkx as nx

class TestComputeMetrics(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.graph_dir = os.path.join(self.temp_dir, 'networks')
        os.makedirs(self.graph_dir)
        self.manifest_path = os.path.join(self.temp_dir, 'network_manifest.json')
        self.metrics_path = os.path.join(self.temp_dir, 'metrics.csv')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_graph(self, mat_id, num_nodes=5, num_edges=4):
        G = nx.Graph()
        for i in range(num_nodes):
            G.add_node(i)
        for i in range(num_edges):
            G.add_edge(i, (i+1) % num_nodes)
        
        data = {
            'graph': G,
            'material_id': mat_id,
            'cif_path': f'/fake/{mat_id}.cif'
        }
        pkl_path = os.path.join(self.graph_dir, f'{mat_id}.pkl')
        with open(pkl_path, 'wb') as f:
            pickle.dump(data, f)
        return pkl_path

    def test_load_graphs_from_directory(self):
        self._create_test_graph('mat1', 5, 4)
        self._create_test_graph('mat2', 3, 2)
        
        graphs = load_graphs_from_directory(self.graph_dir)
        self.assertEqual(len(graphs), 2)
        ids = [g['material_id'] for g in graphs]
        self.assertIn('mat1', ids)
        self.assertIn('mat2', ids)

    def test_load_thermal_conductivity_from_manifest(self):
        manifest_data = {
            'materials': [
                {'material_id': 'mp-1', 'thermal_conductivity_scalar': 10.5},
                {'material_id': 'mp-2', 'thermal_conductivity_scalar': 20.0}
            ]
        }
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        data = load_thermal_conductivity_from_manifest(self.manifest_path)
        self.assertEqual(data['mp-1'], 10.5)
        self.assertEqual(data['mp-2'], 20.0)
        self.assertNotIn('mp-3', data)

    def test_load_physical_descriptors_from_manifest(self):
        manifest_data = {
            'materials': [
                {
                    'material_id': 'mp-1',
                    'unit_cell_volume': 100.0,
                    'total_atom_count': 10,
                    'mean_atomic_mass': 25.5
                }
            ]
        }
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        data = load_physical_descriptors_from_manifest(self.manifest_path)
        self.assertIn('mp-1', data)
        self.assertEqual(data['mp-1']['unit_cell_volume'], 100.0)
        self.assertEqual(data['mp-1']['total_atom_count'], 10)
        self.assertEqual(data['mp-1']['mean_atomic_mass'], 25.5)

    def test_compute_metrics_includes_physical_descriptors(self):
        G = nx.complete_graph(4)
        thermal_data = {'mat1': 15.0}
        physical_data = {
            'mat1': {
                'unit_cell_volume': 50.0,
                'total_atom_count': 8,
                'mean_atomic_mass': 30.0
            }
        }
        
        metrics = compute_metrics_for_graph(G, thermal_data, physical_data, 'mat1')
        
        self.assertEqual(metrics['material_id'], 'mat1')
        self.assertEqual(metrics['thermal_conductivity'], 15.0)
        self.assertEqual(metrics['unit_cell_volume'], 50.0)
        self.assertEqual(metrics['total_atom_count'], 8)
        self.assertEqual(metrics['mean_atomic_mass'], 30.0)

    def test_save_metrics_to_csv_includes_diagnostic_comment(self):
        G = nx.complete_graph(3)
        metrics_list = [
            compute_metrics_for_graph(
                G, 
                {'m1': 10.0}, 
                {'m1': {'unit_cell_volume': 1.0, 'total_atom_count': 2, 'mean_atomic_mass': 3.0}}, 
                'm1'
            )
        ]
        
        save_metrics_to_csv(metrics_list, self.metrics_path, self.manifest_path)
        
        self.assertTrue(os.path.exists(self.metrics_path))
        with open(self.metrics_path, 'r') as f:
            content = f.read()
        
        self.assertIn("# DIAGNOSTICS: Physical descriptors excluded from regression features", content)
        self.assertIn("unit_cell_volume", content)
        self.assertIn("total_atom_count", content)
        self.assertIn("mean_atomic_mass", content)
        self.assertIn("thermal_conductivity", content)

if __name__ == '__main__':
    unittest.main()