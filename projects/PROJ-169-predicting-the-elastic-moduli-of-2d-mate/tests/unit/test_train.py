"""
Unit tests for the training loop in code/model/train.py.
"""
import json
import os
import tempfile
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

# Import the functions we want to test
from model.train import (
    GraphDataset, 
    load_graphs_from_parquet, 
    load_split_indices, 
    filter_graphs_by_split, 
    train_epoch, 
    evaluate,
    get_memory_peak
)
from model.gnn import create_model

class TestTrainPipeline(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary files and mock data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.parquet_path = Path(self.temp_dir) / "test_graphs.parquet"
        self.split_path = Path(self.temp_dir) / "test_splits.json"
        
        # Create mock data
        mock_graphs = []
        for i in range(10):
            mock_graph = {
                "node_features": np.random.rand(5, 10).tolist(), # 5 nodes, 10 features
                "edge_index": [[0, 1, 1, 2], [1, 0, 2, 1]], # 4 edges
                "edge_features": np.random.rand(4, 5).tolist(),
                "target_moduli": np.random.rand(1).tolist()[0],
                "family_id": i % 3
            }
            mock_graphs.append(mock_graph)
        
        # Save to parquet
        df = pd.DataFrame(mock_graphs)
        df.to_parquet(self.parquet_path)
        
        # Save split indices
        split_data = {
            "train": [0, 1, 2, 3, 4, 5],
            "test": [6, 7, 8, 9]
        }
        with open(self.split_path, "w") as f:
            json.dump(split_data, f)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_graphs_from_parquet(self):
        """Test loading graphs from parquet file."""
        graphs = load_graphs_from_parquet(self.parquet_path)
        self.assertEqual(len(graphs), 10)
        self.assertIn("node_features", graphs[0])
        self.assertIn("target_moduli", graphs[0])

    def test_load_split_indices(self):
        """Test loading split indices."""
        splits = load_split_indices(self.split_path)
        self.assertIn("train", splits)
        self.assertIn("test", splits)
        self.assertEqual(len(splits["train"]), 6)

    def test_filter_graphs_by_split(self):
        """Test filtering graphs by split."""
        graphs = load_graphs_from_parquet(self.parquet_path)
        splits = load_split_indices(self.split_path)
        
        train_graphs = filter_graphs_by_split(graphs, splits, "train")
        test_graphs = filter_graphs_by_split(graphs, splits, "test")
        
        self.assertEqual(len(train_graphs), 6)
        self.assertEqual(len(test_graphs), 4)

    def test_graph_dataset_creation(self):
        """Test creating PyTorch Geometric Dataset."""
        graphs = load_graphs_from_parquet(self.parquet_path)
        dataset = GraphDataset(graphs)
        
        self.assertEqual(len(dataset), 10)
        item = dataset[0]
        self.assertIsInstance(item, Data)
        self.assertEqual(item.x.shape[0], 5) # 5 nodes

    def test_model_creation(self):
        """Test model creation."""
        model = create_model(input_dim=10, hidden_dim=16, num_layers=2)
        self.assertIsNotNone(model)

    def test_train_epoch(self):
        """Test training one epoch."""
        graphs = load_graphs_from_parquet(self.parquet_path)
        dataset = GraphDataset(graphs)
        loader = torch_geometric.loader.DataLoader(dataset, batch_size=2, shuffle=True)
        
        model = create_model(input_dim=10, hidden_dim=16, num_layers=2)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        
        loss = train_epoch(model, loader, optimizer, "cpu")
        self.assertGreater(loss, 0)

    def test_evaluate(self):
        """Test evaluation."""
        graphs = load_graphs_from_parquet(self.parquet_path)
        dataset = GraphDataset(graphs)
        loader = torch_geometric.loader.DataLoader(dataset, batch_size=2, shuffle=False)
        
        model = create_model(input_dim=10, hidden_dim=16, num_layers=2)
        
        loss, metrics = evaluate(model, loader, "cpu")
        self.assertGreater(loss, 0)
        self.assertIn("mape", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("r2", metrics)

    def test_memory_check(self):
        """Test memory peak function."""
        mem = get_memory_peak()
        self.assertGreater(mem, 0)

if __name__ == "__main__":
    unittest.main()