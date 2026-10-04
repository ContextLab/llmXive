import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import torch
from torch_geometric.data import Data

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from train import train_ce, save_training_result
from utils import MAX_EPOCHS, CONVERGENCE_THRESHOLD

def test_ce_training_converges():
    """Test that CE training correctly identifies convergence."""
    # Create a simple mock graph
    num_nodes = 10
    num_features = 5
    num_classes = 2
    
    x = torch.randn(num_nodes, num_features)
    edge_index = torch.randint(0, num_nodes, (2, 20))
    y = torch.randint(0, num_classes, (num_nodes,))
    
    graph_data = Data(x=x, edge_index=edge_index, y=y)
    
    # Mock the model to ensure immediate convergence for testing
    with patch('train.build_gcn_model') as mock_build:
        mock_model = MagicMock()
        mock_model.train = MagicMock()
        mock_model.eval = MagicMock()
        mock_model.return_value = torch.randn(num_nodes, num_classes)
        mock_build.return_value = mock_model
        
        with patch('train.compute_accuracy', return_value=0.95):
            result = train_ce(
                graph_data=graph_data,
                graph_id="test_graph",
                beta=0.5,
                node_count=num_nodes,
                seed=42
            )
            
            assert result["convergence_status"] == "converged"
            assert result["steps_to_convergence"] <= MAX_EPOCHS
            assert result["loss_type"] == "cross_entropy"
            assert "trajectory" in result
            assert len(result["trajectory"]) == MAX_EPOCHS

def test_ce_training_censored():
    """Test that CE training correctly identifies censored runs."""
    # Create a simple mock graph
    num_nodes = 10
    num_features = 5
    num_classes = 2
    
    x = torch.randn(num_nodes, num_features)
    edge_index = torch.randint(0, num_nodes, (2, 20))
    y = torch.randint(0, num_classes, (num_nodes,))
    
    graph_data = Data(x=x, edge_index=edge_index, y=y)
    
    # Mock the model to ensure no convergence
    with patch('train.build_gcn_model') as mock_build:
        mock_model = MagicMock()
        mock_model.train = MagicMock()
        mock_model.eval = MagicMock()
        mock_model.return_value = torch.randn(num_nodes, num_classes)
        mock_build.return_value = mock_model
        
        with patch('train.compute_accuracy', return_value=0.50):
            result = train_ce(
                graph_data=graph_data,
                graph_id="test_graph_censored",
                beta=0.5,
                node_count=num_nodes,
                seed=42
            )
            
            assert result["convergence_status"] == "censored"
            assert result["steps_to_convergence"] == MAX_EPOCHS
            assert result["loss_type"] == "cross_entropy"

def test_save_training_result():
    """Test saving training result to JSON file."""
    result = {
        "graph_id": "test_save",
        "loss_type": "cross_entropy",
        "beta": 0.5,
        "node_count": 10,
        "epochs_trained": 100,
        "convergence_status": "converged",
        "steps_to_convergence": 50,
        "final_accuracy": 0.95,
        "final_loss": 0.1,
        "trajectory": [{"loss": 0.5, "accuracy": 0.8}, {"loss": 0.1, "accuracy": 0.95}]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        filepath = save_training_result(result, output_dir)
        
        assert filepath.exists()
        
        with open(filepath, 'r') as f:
            saved_result = json.load(f)
            
        assert saved_result["graph_id"] == result["graph_id"]
        assert saved_result["loss_type"] == result["loss_type"]
        assert saved_result["beta"] == result["beta"]
        assert saved_result["node_count"] == result["node_count"]
        assert saved_result["convergence_status"] == result["convergence_status"]