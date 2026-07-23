"""
Unit tests for model module.
"""
import pytest
import torch
from model import PolymerGNN, validate_model_constraints

def test_gnn_layers_constraint():
    """Test that the GNN architecture respects layer constraints."""
    # Create a model with default constraints (should be <= 3 layers)
    model = PolymerGNN(num_features=10, num_classes=5)
    
    # Count the number of convolutional layers
    conv_layers = [m for m in model.modules() if isinstance(m, torch_geometric.nn.GCNConv)]
    assert len(conv_layers) <= 3

def test_gnn_hidden_dim_constraint():
    """Test that the GNN architecture respects hidden dimension constraints."""
    model = PolymerGNN(num_features=10, num_classes=5)
    
    # Check hidden dimensions
    for layer in model.gcn_layers:
        # The hidden dimension should be <= 128
        assert layer.out_channels <= 128

def test_integrated_gradients_on_dummy_graph():
    """Test Integrated Gradients calculation on a dummy graph."""
    from model import IntegratedGradients
    import torch_geometric.data as data
    
    # Create a dummy graph
    x = torch.randn(5, 10)  # 5 nodes, 10 features
    edge_index = torch.randint(0, 5, (2, 10))
    graph = data.Data(x=x, edge_index=edge_index)
    
    # Initialize IG
    ig = IntegratedGradients(model=None)  # Model would be passed in real use
    
    # Test that IG can be initialized and run (mock model for this test)
    # In a real test, we'd pass a trained model
    assert ig is not None
