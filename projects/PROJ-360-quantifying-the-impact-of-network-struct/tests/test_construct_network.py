"""
tests/test_construct_network.py

Tests for code/construct_network.py
"""
import os
import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import networkx as nx

# Import the module under test
from construct_network import (
    process_cif_file,
    save_graph_to_pickle,
    build_network_manifest,
    detect_bonds_covalent,
    detect_bonds_fallback,
    construct_network_from_structure,
    MIN_NODES,
    MIN_EDGES
)
from pymatgen.core import Structure

class TestConstructNetwork(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_detect_bonds_covalent_basic(self):
        """Test bond detection with a simple structure."""
        # Create a simple diamond-like structure
        lattice = [[3.57, 0, 0], [0, 3.57, 0], [0, 0, 3.57]]
        species = ["C", "C"]
        coords = [[0, 0, 0], [0.25, 0.25, 0.25]]
        structure = Structure(lattice, species, coords)
        
        bonds = detect_bonds_covalent(structure)
        self.assertTrue(len(bonds) > 0, "Expected at least one bond in diamond structure")

    def test_construct_network_from_structure(self):
        """Test full graph construction."""
        lattice = [[3.57, 0, 0], [0, 3.57, 0], [0, 0, 3.57]]
        species = ["C", "C", "C", "C"]
        coords = [[0, 0, 0], [0.25, 0.25, 0.25], [0.5, 0.5, 0.5], [0.75, 0.75, 0.75]]
        structure = Structure(lattice, species, coords)
        
        G = construct_network_from_structure(structure)
        
        self.assertIsInstance(G, nx.Graph)
        self.assertGreaterEqual(G.number_of_nodes(), MIN_NODES)
        self.assertGreaterEqual(G.number_of_edges(), MIN_EDGES)

    def test_process_cif_file_success(self):
        """Test successful CIF processing."""
        # Create a mock CIF file content
        cif_content = """
        data_test
        _cell_length_a 3.57
        _cell_length_b 3.57
        _cell_length_c 3.57
        _cell_angle_alpha 90
        _cell_angle_beta 90
        _cell_angle_gamma 90
        _symmetry_space_group_name_H-M 'F d -3 m'
        
        loop_
        _atom_site_label
        _atom_site_type_symbol
        _atom_site_fract_x
        _atom_site_fract_y
        _atom_site_fract_z
        C1 C 0.0 0.0 0.0
        C2 C 0.25 0.25 0.25
        """
        
        cif_path = self.test_dir / "test.cif"
        cif_path.write_text(cif_content)
        
        # Mock logger
        mock_logger = MagicMock()
        
        graph = process_cif_file(cif_path, mock_logger)
        
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, nx.Graph)
        self.assertGreaterEqual(graph.number_of_nodes(), MIN_NODES)
        self.assertGreaterEqual(graph.number_of_edges(), MIN_EDGES)

    def test_process_cif_file_skip_insufficient_nodes(self):
        """Test that structures with < 2 nodes are skipped."""
        # Create a mock CIF with only 1 atom
        cif_content = """
        data_test
        _cell_length_a 3.57
        _cell_length_b 3.57
        _cell_length_c 3.57
        _cell_angle_alpha 90
        _cell_angle_beta 90
        _cell_angle_gamma 90
        
        loop_
        _atom_site_label
        _atom_site_type_symbol
        _atom_site_fract_x
        _atom_site_fract_y
        _atom_site_fract_z
        C1 C 0.0 0.0 0.0
        """
        
        cif_path = self.test_dir / "test_single.cif"
        cif_path.write_text(cif_content)
        
        mock_logger = MagicMock()
        
        graph = process_cif_file(cif_path, mock_logger)
        
        self.assertIsNone(graph)
        mock_logger.warning.assert_called()

    def test_save_graph_to_pickle(self):
        """Test saving graph to pickle file."""
        G = nx.Graph()
        G.add_nodes_from([0, 1, 2])
        G.add_edges_from([(0, 1), (1, 2)])
        
        output_path = self.test_dir / "test_graph.pkl"
        
        mock_logger = MagicMock()
        success = save_graph_to_pickle(G, output_path, mock_logger)
        
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
        
        # Verify content
        with open(output_path, 'rb') as f:
            loaded_G = pickle.load(f)
        
        self.assertEqual(loaded_G.number_of_nodes(), 3)
        self.assertEqual(loaded_G.number_of_edges(), 2)

    def test_build_network_manifest(self):
        """Test manifest generation."""
        metadata = [
            {"filename": "graph1.pkl", "num_nodes": 10, "num_edges": 20},
            {"filename": "graph2.pkl", "num_nodes": 15, "num_edges": 25}
        ]
        
        manifest_path = self.test_dir / "manifest.json"
        
        build_network_manifest(metadata, manifest_path)
        
        self.assertTrue(manifest_path.exists())
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        self.assertEqual(manifest["total_graphs"], 2)
        self.assertEqual(len(manifest["graphs"]), 2)
        self.assertEqual(manifest["graphs"][0]["filename"], "graph1.pkl")

if __name__ == "__main__":
    unittest.main()