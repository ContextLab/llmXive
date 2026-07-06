"""
Unit tests for SchNet architecture initialization.
Task: T022 [P] [US2] Unit test for SchNet architecture initialization in tests/unit/test_models.py
"""
import pytest
import torch
from torch_geometric.data import Data
from torch_geometric.nn import SchNet
from pathlib import Path
import sys

# Ensure the project root is in the path if running standalone, 
# though typically pytest handles this via conftest or setup.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

class TestSchNetArchitectureInitialization:
    """Tests for verifying SchNet model initialization parameters and structure."""

    def test_schnet_initialization_basic(self):
        """Test basic SchNet initialization with standard parameters."""
        # Standard parameters for QM9-TS like tasks
        num_features = 12  # Atomic number, charge, etc.
        hidden_channels = 128
        num_filters = 128
        num_interactions = 3
        num_gaussians = 50
        cutoff = 3.5  # Angstroms, matching graph_construction logic

        model = SchNet(
            num_features=num_features,
            hidden_channels=hidden_channels,
            num_filters=num_filters,
            num_interactions=num_interactions,
            num_gaussians=num_gaussians,
            cutoff=cutoff,
            readout='add'
        )

        assert model is not None
        assert model.num_features == num_features
        assert model.hidden_channels == hidden_channels
        assert model.num_filters == num_filters
        assert model.num_interactions == num_interactions
        assert model.num_gaussians == num_gaussians
        assert model.cutoff == cutoff

    def test_schnet_initialization_with_output_dim(self):
        """Test SchNet initialization with specific output dimension for energy prediction."""
        model = SchNet(
            num_features=12,
            hidden_channels=64,
            num_filters=64,
            num_interactions=2,
            num_gaussians=30,
            cutoff=3.5,
            readout='add'
        )
        
        # Verify the model has a linear layer at the end for regression
        # SchNet typically ends with a sequential block
        assert hasattr(model, 'readout') or hasattr(model, 'lin')

    def test_schnet_forward_pass_dummy_data(self):
        """Test that the initialized model can perform a forward pass on dummy data."""
        model = SchNet(
            num_features=12,
            hidden_channels=32,
            num_filters=32,
            num_interactions=2,
            num_gaussians=20,
            cutoff=3.5,
            readout='add'
        )

        # Create a dummy graph
        # Nodes: 5 atoms
        # Edges: simple connectivity
        num_nodes = 5
        x = torch.randn(num_nodes, 12)  # Node features
        pos = torch.randn(num_nodes, 3)  # Atomic positions
        
        # Create a simple edge index (fully connected for simplicity in test)
        edge_index = torch.randint(0, num_nodes, (2, 20))
        edge_attr = torch.randn(20, 20) # Distance features (simplified)

        # Construct PyTorch Geometric Data object
        data = Data(x=x, pos=pos, edge_index=edge_index)

        # Forward pass
        try:
            out = model(data)
            assert out.shape[0] == 1  # Single graph output
            assert out.dim() == 1 or out.dim() == 2
        except Exception as e:
            pytest.fail(f"Forward pass failed: {e}")

    def test_schnet_cpu_compatibility(self):
        """Ensure the model can be instantiated and run on CPU."""
        model = SchNet(
            num_features=12,
            hidden_channels=32,
            num_filters=32,
            num_interactions=2,
            num_gaussians=20,
            cutoff=3.5,
            readout='add'
        )
        
        # Explicitly move to CPU to verify compatibility
        model = model.to('cpu')
        assert next(model.parameters()).device.type == 'cpu'

    def test_schnet_parameter_count(self):
        """Verify that the model has a reasonable number of parameters."""
        model = SchNet(
            num_features=12,
            hidden_channels=64,
            num_filters=64,
            num_interactions=3,
            num_gaussians=50,
            cutoff=3.5,
            readout='add'
        )
        
        total_params = sum(p.numel() for p in model.parameters())
        assert total_params > 0
        # Sanity check: should be in the range of tens/hundreds of thousands for this config
        assert 1000 < total_params < 10000000