"""
Unit tests for the GNN model implementation (T030).
"""

import pytest
import torch
from torch_geometric.data import Data

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from model.gnn import StaticScatteringPotentialGNN


def test_model_initialization():
    """Test that the model initializes correctly with expected parameters."""
    input_dim = 5
    hidden_dim = 16
    model = StaticScatteringPotentialGNN(input_dim=input_dim, hidden_dim=hidden_dim)

    assert model.param_count < 1_000_000, "Model exceeds 1M parameter limit"
    assert isinstance(model, torch.nn.Module)


def test_forward_pass_single_graph():
    """Test forward pass with a single graph."""
    input_dim = 5
    hidden_dim = 16
    model = StaticScatteringPotentialGNN(input_dim=input_dim, hidden_dim=hidden_dim)
    model.eval()

    # Create a dummy graph
    num_nodes = 10
    x = torch.randn(num_nodes, input_dim)
    edge_index = torch.randint(0, num_nodes, (2, 20))
    batch = torch.zeros(num_nodes, dtype=torch.long)

    with torch.no_grad():
        out = model(x, edge_index, batch)

    assert out.shape == (1, 1), f"Expected output shape (1, 1), got {out.shape}"


def test_forward_pass_batch():
    """Test forward pass with a batch of graphs."""
    input_dim = 5
    hidden_dim = 16
    model = StaticScatteringPotentialGNN(input_dim=input_dim, hidden_dim=hidden_dim)
    model.eval()

    # Create two graphs
    x1 = torch.randn(5, input_dim)
    edge_index1 = torch.randint(0, 5, (2, 10))
    batch1 = torch.zeros(5, dtype=torch.long)

    x2 = torch.randn(8, input_dim)
    edge_index2 = torch.randint(0, 8, (2, 15))
    batch2 = torch.ones(8, dtype=torch.long)

    x = torch.cat([x1, x2], dim=0)
    # Adjust edge_index for second graph
    edge_index2_adj = edge_index2 + 5
    edge_index = torch.cat([edge_index1, edge_index2_adj], dim=1)
    batch = torch.cat([batch1, batch2], dim=0)

    with torch.no_grad():
        out = model(x, edge_index, batch)

    assert out.shape == (2, 1), f"Expected output shape (2, 1), got {out.shape}"