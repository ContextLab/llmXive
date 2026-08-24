"""
Tests for the Connectivity-only GNN (2D) Baseline Architecture.
"""
import torch
from torch_geometric.data import Data

from models.baseline_2d import Baseline2DModel, create_baseline_2d_model
from data.dataset import MoleculeData


def test_baseline_2d_initialization():
    """Test that the model initializes correctly."""
    model = create_baseline_2d_model(num_atom_types=128, hidden_channels=64, num_layers=2)
    assert isinstance(model, Baseline2DModel)
    assert model.hidden_channels == 64
    assert model.num_layers == 2
    # Check that it has parameters
    assert sum(p.numel() for p in model.parameters()) > 0


def test_baseline_2d_forward_pass():
    """Test forward pass with dummy data."""
    model = create_baseline_2d_model(num_atom_types=128, hidden_channels=64, num_layers=2)
    model.eval()

    # Create dummy molecule data
    # 5 atoms, atomic numbers 6 (Carbon)
    x = torch.tensor([[6], [6], [6], [6], [6]], dtype=torch.float)
    # Simple chain: 0-1, 1-2, 2-3, 3-4
    edge_index = torch.tensor([
        [0, 1, 2, 3],
        [1, 2, 3, 4]
    ], dtype=torch.long)

    # Create MoleculeData object
    # Note: pos is provided but model should ignore it
    pos = torch.tensor([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
        [4.0, 0.0, 0.0]
    ], dtype=torch.float)

    data = MoleculeData(x=x, edge_index=edge_index, pos=pos, y=torch.zeros(5, 1))

    # Run forward pass
    with torch.no_grad():
        output = model(data)

    # Check output shape: [N, 1]
    assert output.shape == (5, 1)
    assert output.dtype == torch.float32


def test_baseline_2d_ignores_pos():
    """Verify that the model produces the same output regardless of pos."""
    model = create_baseline_2d_model(num_atom_types=128, hidden_channels=64, num_layers=2)
    model.eval()

    x = torch.tensor([[6], [6]], dtype=torch.float)
    edge_index = torch.tensor([[0], [1]], dtype=torch.long)

    # Case 1: Pos at origin
    pos1 = torch.tensor([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=torch.float)
    data1 = MoleculeData(x=x, edge_index=edge_index, pos=pos1, y=torch.zeros(2, 1))

    # Case 2: Pos far apart
    pos2 = torch.tensor([[0.0, 0.0, 0.0], [100.0, 0.0, 0.0]], dtype=torch.float)
    data2 = MoleculeData(x=x, edge_index=edge_index, pos=pos2, y=torch.zeros(2, 1))

    with torch.no_grad():
        out1 = model(data1)
        out2 = model(data2)

    # Outputs should be identical because pos is ignored
    assert torch.allclose(out1, out2)


def test_baseline_2d_batch_compatibility():
    """Test that the model can handle batched data (conceptually)."""
    model = create_baseline_2d_model(num_atom_types=128, hidden_channels=64, num_layers=2)
    model.eval()

    # Simulate a batch of 2 molecules manually by concatenating
    # Mol 1: 2 atoms
    x1 = torch.tensor([[6], [6]], dtype=torch.float)
    edge1 = torch.tensor([[0], [1]], dtype=torch.long)

    # Mol 2: 3 atoms
    x2 = torch.tensor([[8], [8], [8]], dtype=torch.float) # Oxygen
    edge2 = torch.tensor([[0, 1], [1, 2]], dtype=torch.long) # 0-1, 1-2

    # Batched
    x_batch = torch.cat([x1, x2], dim=0)
    # Adjust edge indices for mol 2 (offset by 2)
    edge2_offset = edge2 + 2
    edge_index_batch = torch.cat([edge1, edge2_offset], dim=1)

    data_batch = MoleculeData(
        x=x_batch,
        edge_index=edge_index_batch,
        pos=torch.zeros(5, 3),
        y=torch.zeros(5, 1),
        batch=torch.tensor([0, 0, 1, 1, 1]) # Not strictly used in forward, but good for completeness
    )

    with torch.no_grad():
        output = model(data_batch)

    assert output.shape == (5, 1)