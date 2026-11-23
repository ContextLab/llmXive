"""
Unit tests for GCN model implementation.
"""
import pytest
import torch
from torch_geometric.data import Data
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.models.gcn import GCN, create_gcn_model, count_parameters

@pytest.fixture
def dummy_data():
    """Create a dummy graph for testing."""
    num_nodes = 10
    num_edges = 20
    input_dim = 10
    
    x = torch.randn(num_nodes, input_dim)
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    batch = torch.zeros(num_nodes, dtype=torch.long)
    
    return Data(x=x, edge_index=edge_index, batch=batch)

@pytest.fixture
def dummy_model():
    """Create a dummy GCN model."""
    return create_gcn_model(input_dim=10, hidden_dim=16, num_layers=1)

def test_gcn_initialization():
    """Test that GCN model initializes correctly."""
    model = GCN(input_dim=10, hidden_dim=16, num_layers=1)
    assert model.num_layers == 1
    assert model.dropout == 0.5
    
    # Check that layers exist
    assert hasattr(model, 'conv1')
    assert hasattr(model, 'bn1')
    assert hasattr(model, 'fc')
    
    # Check hidden dimension
    assert model.conv1.out_channels == 16

def test_gcn_two_layers():
    """Test GCN with 2 layers."""
    model = GCN(input_dim=10, hidden_dim=16, num_layers=2)
    assert model.num_layers == 2
    assert hasattr(model, 'conv2')
    assert hasattr(model, 'bn2')

def test_gcn_forward_pass(dummy_data, dummy_model):
    """Test forward pass produces valid output."""
    dummy_model.eval()
    with torch.no_grad():
        output = dummy_model(dummy_data)
    
    # Output should be (num_graphs, output_dim)
    assert output.shape[0] == 1  # Single graph in batch
    assert output.shape[1] == 1  # Single output dimension

def test_gcn_batched_forward():
    """Test forward pass with batched graphs."""
    # Create batch of 2 graphs
    num_nodes_per_graph = 5
    num_graphs = 2
    input_dim = 10
    
    x = torch.randn(num_nodes_per_graph * num_graphs, input_dim)
    edge_index = torch.randint(0, num_nodes_per_graph * num_graphs, (2, 10))
    batch = torch.arange(num_graphs).repeat_interleave(num_nodes_per_graph)
    
    data = Data(x=x, edge_index=edge_index, batch=batch)
    
    model = create_gcn_model(input_dim=input_dim, hidden_dim=16, num_layers=1)
    model.eval()
    
    with torch.no_grad():
        output = model(data)
    
    # Output should be (num_graphs, output_dim)
    assert output.shape[0] == num_graphs
    assert output.shape[1] == 1

def test_gcn_parameter_count():
    """Test parameter counting function."""
    model = create_gcn_model(input_dim=10, hidden_dim=16, num_layers=1)
    params = count_parameters(model)
    assert params > 0

def test_gcn_max_layers_constraint():
    """Test that num_layers > 2 is clamped to 2."""
    model = GCN(input_dim=10, hidden_dim=16, num_layers=3)
    assert model.num_layers == 2

def test_gcn_min_layers_constraint():
    """Test that num_layers < 1 raises error."""
    with pytest.raises(ValueError):
        GCN(input_dim=10, hidden_dim=16, num_layers=0)

def test_gcn_device_placement():
    """Test that model is placed on correct device."""
    model = create_gcn_model(input_dim=10)
    # Check that model parameters are on CPU (as per config)
    for param in model.parameters():
        assert param.device.type == 'cpu'
