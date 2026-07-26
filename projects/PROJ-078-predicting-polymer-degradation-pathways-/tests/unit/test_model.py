"""Unit tests for GNN model constraints."""
import pytest
import torch
from model import PolymerGNN, validate_model_constraints

class TestGNNConstraints:
    def test_gnn_layers_constraint(self):
        """Test that the GNN respects the layer constraint (<=3)."""
        # Create a model with 3 layers (max allowed)
        model = PolymerGNN(input_dim=64, hidden_dim=128, num_layers=3, output_dim=2)
        is_valid, msg = validate_model_constraints(model)
        assert is_valid, f"Model with 3 layers should be valid: {msg}"

        # Create a model with 4 layers (exceeds limit)
        model_bad = PolymerGNN(input_dim=64, hidden_dim=128, num_layers=4, output_dim=2)
        is_valid, msg = validate_model_constraints(model_bad)
        assert not is_valid, "Model with 4 layers should be invalid"

    def test_gnn_hidden_dim_constraint(self):
        """Test that the GNN respects the hidden dimension constraint (<=128)."""
        # Create a model with 128 hidden dim (max allowed)
        model = PolymerGNN(input_dim=64, hidden_dim=128, num_layers=2, output_dim=2)
        is_valid, msg = validate_model_constraints(model)
        assert is_valid, f"Model with 128 hidden dim should be valid: {msg}"

        # Create a model with 256 hidden dim (exceeds limit)
        model_bad = PolymerGNN(input_dim=64, hidden_dim=256, num_layers=2, output_dim=2)
        is_valid, msg = validate_model_constraints(model_bad)
        assert not is_valid, "Model with 256 hidden dim should be invalid"

    def test_integrated_gradients_on_dummy_graph(self):
        """Test IntegratedGradients calculation on a dummy graph."""
        from model import IntegratedGradients
        from torch_geometric.data import Data

        # Create a dummy graph
        x = torch.randn(5, 10)  # 5 nodes, 10 features
        edge_index = torch.randint(0, 5, (2, 10))
        data = Data(x=x, edge_index=edge_index)

        # Initialize IG
        ig = IntegratedGradients()

        # Run on a dummy model (PolymerGNN)
        model = PolymerGNN(input_dim=10, hidden_dim=16, num_layers=2, output_dim=2)
        model.eval()

        # Calculate attributions
        attributions = ig.attribute(model, data)

        assert attributions is not None
        assert attributions.shape == x.shape
