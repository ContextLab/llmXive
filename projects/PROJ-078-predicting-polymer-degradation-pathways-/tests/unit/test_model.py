import pytest
import torch
from torch_geometric.data import Data

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from model import PolymerGNN, IntegratedGradients, create_model_from_config, validate_model_constraints, MAX_LAYERS, MAX_HIDDEN_DIM


class TestPolymerGNNArchitecture:
    """Tests for the GNN architecture constraints and structure."""

    def test_gnn_layers_constraint(self):
        """Test that model rejects layers > 3."""
        with pytest.raises(ValueError):
            create_model_from_config({
                "num_features": 10,
                "num_classes": 3,
                "hidden_dim": 64,
                "num_layers": 4  # Exceeds MAX_LAYERS
            })

    def test_gnn_hidden_dim_constraint(self):
        """Test that model rejects hidden_dim > 128."""
        with pytest.raises(ValueError):
            create_model_from_config({
                "num_features": 10,
                "num_classes": 3,
                "hidden_dim": 256, # Exceeds MAX_HIDDEN_DIM
                "num_layers": 2
            })

    def test_valid_model_creation(self):
        """Test creation of a valid model within constraints."""
        model = create_model_from_config({
            "num_features": 10,
            "num_classes": 3,
            "hidden_dim": 128,
            "num_layers": 3
        })
        assert model.num_layers == 3
        assert model.hidden_dim == 128
        assert validate_model_constraints(model)

    def test_forward_pass_shape(self):
        """Test that forward pass produces correct output shape."""
        model = create_model_from_config({
            "num_features": 10,
            "num_classes": 3,
            "hidden_dim": 64,
            "num_layers": 2
        })
        
        # Create dummy graph
        num_nodes = 10
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, 20))
        batch = torch.zeros(num_nodes, dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index, batch=batch)
        
        model.eval()
        with torch.no_grad():
            output = model(data)
        
        # Output should be [num_graphs, num_classes] = [1, 3]
        assert output.shape == (1, 3)


class TestIntegratedGradients:
    """Tests for the Integrated Gradients implementation."""

    def test_integrated_gradients_on_dummy_graph(self):
        """Test IG calculation on a simple dummy graph."""
        model = create_model_from_config({
            "num_features": 5,
            "num_classes": 2,
            "hidden_dim": 16,
            "num_layers": 2
        })
        
        # Create dummy data
        num_nodes = 5
        x = torch.randn(num_nodes, 5)
        edge_index = torch.randint(0, num_nodes, (2, 8))
        batch = torch.zeros(num_nodes, dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index, batch=batch)
        
        # Run IG
        ig = IntegratedGradients(model, n_steps=10)
        scores = ig.compute(data)
        
        # Check output shape and type
        assert scores.shape == (num_nodes, 5)
        assert scores.dtype == torch.float32
        
        # Check that scores are non-zero (unless input is zero)
        # Since input is random, gradients should exist
        assert not torch.allclose(scores, torch.zeros_like(scores))

    def test_integrated_gradients_reproducibility(self):
        """Test that IG is deterministic for fixed input."""
        model = create_model_from_config({
            "num_features": 5,
            "num_classes": 2,
            "hidden_dim": 16,
            "num_layers": 2
        })
        
        num_nodes = 5
        x = torch.randn(num_nodes, 5)
        edge_index = torch.randint(0, num_nodes, (2, 8))
        batch = torch.zeros(num_nodes, dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index, batch=batch)
        
        ig = IntegratedGradients(model, n_steps=10)
        scores1 = ig.compute(data)
        scores2 = ig.compute(data)
        
        assert torch.allclose(scores1, scores2)
