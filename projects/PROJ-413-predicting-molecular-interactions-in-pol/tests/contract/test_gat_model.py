"""
Contract test for GAT model architecture definition.

This test verifies that the Graph Attention Network (GAT) model defined in
code/models/gat.py adheres to the architectural constraints specified in the
project plan:
- 3 layers of GATConv
- Hidden dimension = 64
- Dropout = 0.5
- Uses torch_geometric.nn.GATConv
"""

import sys
import os
import pytest
import torch
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from models.gat import GATModel
from torch_geometric.nn import GATConv


class TestGATModelArchitecture:
    """Contract tests for GAT model architecture."""

    def test_model_instantiation(self):
        """Test that the model can be instantiated with default parameters."""
        model = GATModel(
            in_channels=10,  # Dummy input dimension
            hidden_channels=64,
            out_channels=1,
            num_layers=3,
            dropout=0.5
        )
        assert model is not None

    def test_num_gat_conv_layers(self):
        """Verify exactly 3 GATConv layers are present."""
        model = GATModel(
            in_channels=10,
            hidden_channels=64,
            out_channels=1,
            num_layers=3,
            dropout=0.5
        )
        
        gat_conv_count = sum(1 for module in model.modules() if isinstance(module, GATConv))
        assert gat_conv_count == 3, f"Expected 3 GATConv layers, found {gat_conv_count}"

    def test_hidden_dimension(self):
        """Verify hidden dimension is 64."""
        model = GATModel(
            in_channels=10,
            hidden_channels=64,
            out_channels=1,
            num_layers=3,
            dropout=0.5
        )
        
        # Check first hidden layer dimension
        assert model.gnn[0].in_channels == 10
        assert model.gnn[0].out_channels == 64
        
        # Check subsequent hidden layers
        for i in range(1, len(model.gnn)):
            assert model.gnn[i].in_channels == 64
            assert model.gnn[i].out_channels == 64

    def test_dropout_value(self):
        """Verify dropout is set to 0.5."""
        model = GATModel(
            in_channels=10,
            hidden_channels=64,
            out_channels=1,
            num_layers=3,
            dropout=0.5
        )
        
        # Check that dropout layers exist and have correct value
        dropout_layers = [m for m in model.modules() if isinstance(m, torch.nn.Dropout)]
        assert len(dropout_layers) > 0, "No Dropout layers found"
        
        for dropout_layer in dropout_layers:
            assert dropout_layer.p == 0.5, f"Expected dropout=0.5, got {dropout_layer.p}"

    def test_forward_pass_shape(self):
        """Verify forward pass produces correct output shape."""
        model = GATModel(
            in_channels=10,
            hidden_channels=64,
            out_channels=1,
            num_layers=3,
            dropout=0.5
        )
        model.eval()

        # Create dummy graph
        num_nodes = 20
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, 50))

        with torch.no_grad():
            out = model(x, edge_index)
        
        # Output should be (num_graphs, out_channels) -> (1, 1) for single graph
        assert out.shape == (1, 1), f"Expected output shape (1, 1), got {out.shape}"

    def test_model_uses_gatconv(self):
        """Verify model uses GATConv from torch_geometric.nn."""
        model = GATModel(
            in_channels=10,
            hidden_channels=64,
            out_channels=1,
            num_layers=3,
            dropout=0.5
        )
        
        # Verify all convolution layers are GATConv
        for module in model.modules():
            if isinstance(module, (torch.nn.Module)):
                if hasattr(module, 'in_channels') and hasattr(module, 'out_channels'):
                    assert isinstance(module, GATConv) or not (hasattr(module, 'in_channels')), \
                        f"Expected GATConv, found {type(module)}"

    def test_model_parameters_count(self):
        """Verify model has reasonable parameter count (sanity check)."""
        model = GATModel(
            in_channels=10,
            hidden_channels=64,
            out_channels=1,
            num_layers=3,
            dropout=0.5
        )
        
        total_params = sum(p.numel() for p in model.parameters())
        assert total_params > 0, "Model has no parameters"
        # GAT with 3 layers, hidden=64, input=10 should have ~10k-50k params
        assert 1000 < total_params < 200000, f"Unexpected parameter count: {total_params}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])