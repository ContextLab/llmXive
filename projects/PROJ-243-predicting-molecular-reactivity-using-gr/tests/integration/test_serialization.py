import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

import torch
from torch_geometric.data import Data

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from config import get_config, ensure_directories
from serialization import (
    load_intermediate_graphs,
    load_split_indices,
    filter_graphs_by_indices,
    validate_graph_schema,
    serialize_graphs,
    write_derivation_log,
    main
)


class TestSerialization(unittest.TestCase):
    """Integration tests for the serialization task (T016)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.intermediate_file = os.path.join(self.test_dir, "graphs_intermediate.pt")
        self.split_dir = os.path.join(self.test_dir, "splits")
        os.makedirs(self.split_dir, exist_ok=True)
        
        # Create test graphs
        self.test_graphs = []
        for i in range(10):
            graph = Data(
                x=torch.randn(5, 10),  # 5 nodes, 10 features
                edge_index=torch.randint(0, 5, (2, 20)),  # 20 edges
                y=torch.tensor([i % 2])  # Binary label
            )
            self.test_graphs.append(graph)
        
        # Save intermediate graphs
        torch.save(self.test_graphs, self.intermediate_file)
        
        # Create split indices
        self.train_indices = [0, 1, 2, 3, 4]
        self.val_indices = [5, 6]
        self.test_indices = [7, 8, 9]
        
        torch.save(self.train_indices, os.path.join(self.split_dir, "train_indices.pt"))
        torch.save(self.val_indices, os.path.join(self.split_dir, "val_indices.pt"))
        torch.save(self.test_indices, os.path.join(self.split_dir, "test_indices.pt"))

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_intermediate_graphs(self):
        """Test loading intermediate graphs."""
        graphs = load_intermediate_graphs(self.intermediate_file)
        self.assertEqual(len(graphs), 10)
        self.assertIsInstance(graphs[0], Data)
        self.assertEqual(graphs[0].x.shape, (5, 10))

    def test_load_split_indices(self):
        """Test loading split indices."""
        train, val, test = load_split_indices(self.split_dir)
        self.assertEqual(train, self.train_indices)
        self.assertEqual(val, self.val_indices)
        self.assertEqual(test, self.test_indices)

    def test_filter_graphs_by_indices(self):
        """Test filtering graphs by indices."""
        filtered = filter_graphs_by_indices(self.test_graphs, [0, 2, 4])
        self.assertEqual(len(filtered), 3)
        self.assertEqual(filtered[0], self.test_graphs[0])
        self.assertEqual(filtered[1], self.test_graphs[2])
        self.assertEqual(filtered[2], self.test_graphs[4])

    def test_validate_graph_schema_valid(self):
        """Test validation of a valid graph."""
        graph = Data(
            x=torch.randn(5, 10),
            edge_index=torch.randint(0, 5, (2, 20)),
            y=torch.tensor([0])
        )
        result = validate_graph_schema(graph)
        self.assertTrue(result)

    def test_validate_graph_schema_missing_attr(self):
        """Test validation fails for missing attribute."""
        graph = Data(
            x=torch.randn(5, 10),
            edge_index=torch.randint(0, 5, (2, 20))
            # Missing 'y'
        )
        with self.assertRaises(ValueError):
            validate_graph_schema(graph)

    def test_validate_graph_schema_invalid_edge_index(self):
        """Test validation fails for invalid edge_index shape."""
        graph = Data(
            x=torch.randn(5, 10),
            edge_index=torch.randint(0, 5, (3, 20)),  # Wrong shape
            y=torch.tensor([0])
        )
        with self.assertRaises(ValueError):
            validate_graph_schema(graph)

    def test_serialize_graphs(self):
        """Test serialization of graphs."""
        output_path = os.path.join(self.test_dir, "graphs.pt")
        serialize_graphs(self.test_graphs, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 0)
        
        # Verify loaded graphs match
        loaded = torch.load(output_path, weights_only=False)
        self.assertEqual(len(loaded), len(self.test_graphs))

    def test_write_derivation_log(self):
        """Test writing derivation log."""
        output_path = os.path.join(self.test_dir, "graphs.pt")
        split_files = {
            "train": os.path.join(self.split_dir, "train_indices.pt"),
            "val": os.path.join(self.split_dir, "val_indices.pt"),
            "test": os.path.join(self.split_dir, "test_indices.pt")
        }
        counts = {"train": 5, "val": 2, "test": 3}
        
        write_derivation_log(self.intermediate_file, split_files, output_path, counts)
        
        log_path = output_path.replace(".pt", "_derivation.json")
        self.assertTrue(os.path.exists(log_path))
        
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["total_graphs"], 10)
        self.assertEqual(log_data["process"], "T016_serialization")

    def test_full_serialization_flow(self):
        """Test the complete serialization flow."""
        # Load intermediate graphs
        graphs = load_intermediate_graphs(self.intermediate_file)
        
        # Load split indices
        train_idx, val_idx, test_idx = load_split_indices(self.split_dir)
        
        # Filter graphs
        train_graphs = filter_graphs_by_indices(graphs, train_idx)
        val_graphs = filter_graphs_by_indices(graphs, val_idx)
        test_graphs = filter_graphs_by_indices(graphs, test_idx)
        
        # Combine and serialize
        final_graphs = train_graphs + val_graphs + test_graphs
        output_path = os.path.join(self.test_dir, "graphs_final.pt")
        serialize_graphs(final_graphs, output_path)
        
        # Verify
        loaded = torch.load(output_path, weights_only=False)
        self.assertEqual(len(loaded), 10)
        
        # Verify split composition
        self.assertEqual(len(train_graphs), 5)
        self.assertEqual(len(val_graphs), 2)
        self.assertEqual(len(test_graphs), 3)


if __name__ == "__main__":
    unittest.main()