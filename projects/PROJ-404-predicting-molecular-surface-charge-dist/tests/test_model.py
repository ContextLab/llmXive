"""
Tests for the SchNet model architecture.
"""
import pytest
import torch
from torch_geometric.data import Data

# Import the model class and factory
from models.schnet import SchNet, build_schnet_model


class TestSchNetArchitecture:
    """Unit tests for SchNet architecture initialization and basic forward pass."""

    def test_model_initialization(self):
        """Test that the model initializes with correct parameters."""
        config = {
            'num_filters': 64,
            'num_gaussians': 32,
            'num_interaction_blocks': 2
        }
        model = build_schnet_model(config)
        
        assert model.hidden_channels == 64
        assert model.num_gaussians == 32
        assert model.num_interaction_blocks == 2
        assert len(model.interactions) == 2

    def test_forward_pass_single_molecule(self):
        """Test forward pass with a single small molecule."""
        # Create dummy data
        # Atomic numbers (C, H, H)
        x = torch.tensor([6, 1, 1], dtype=torch.long)
        # Positions
        pos = torch.tensor([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ], dtype=torch.float)
        
        # Edges: 0-1, 0-2
        edge_index = torch.tensor([
            [0, 0, 1, 2],
            [1, 2, 0, 0]
        ], dtype=torch.long)
        
        # Distances (approximate)
        edge_attr = torch.tensor([1.0, 1.0, 1.0, 1.0], dtype=torch.float)

        data = Data(x=x, pos=pos, edge_index=edge_index, edge_attr=edge_attr)

        # Initialize model
        model = SchNet(
            num_atom_types=100,
            hidden_channels=64,
            num_gaussians=32,
            num_interaction_blocks=2
        )
        model.eval()

        with torch.no_grad():
            output = model(data)

        # Output should be (num_atoms, 1)
        assert output.shape == (3, 1)
        assert not torch.isnan(output).any()

    def test_forward_pass_batch(self):
        """Test forward pass with a batch of molecules."""
        # Create batched data manually (simplified)
        # Molecule 1: 2 atoms, Molecule 2: 3 atoms
        x = torch.tensor([6, 1, 6, 1, 1], dtype=torch.long)
        pos = torch.tensor([
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], # Mol 1
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0] # Mol 2
        ], dtype=torch.float)
        
        # Edges for Mol 1 (0-1) and Mol 2 (2-3, 2-4)
        edge_index = torch.tensor([
            [0, 2, 2],
            [1, 3, 4]
        ], dtype=torch.long)
        
        edge_attr = torch.tensor([1.0, 1.0, 1.0], dtype=torch.float)

        data = Data(x=x, pos=pos, edge_index=edge_index, edge_attr=edge_attr)

        model = SchNet(
            num_atom_types=100,
            hidden_channels=64,
            num_gaussians=32,
            num_interaction_blocks=2
        )
        model.eval()

        with torch.no_grad():
            output = model(data)

        assert output.shape == (5, 1)

    def test_model_device_placement(self):
        """Test that model parameters are on the correct device."""
        model = SchNet(num_atom_types=100, hidden_channels=64, num_gaussians=32, num_interaction_blocks=2)
        
        # Check default device (CPU)
        for param in model.parameters():
            assert param.device.type == 'cpu'

        # If CUDA is available, test moving to GPU
        if torch.cuda.is_available():
            model = model.cuda()
            for param in model.parameters():
                assert param.device.type == 'cuda'

    def test_gradient_flow(self):
        """Test that gradients flow through the network."""
        model = SchNet(num_atom_types=100, hidden_channels=64, num_gaussians=32, num_interaction_blocks=2)
        model.train()

        x = torch.tensor([6, 1], dtype=torch.long)
        pos = torch.tensor([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=torch.float)
        edge_index = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
        edge_attr = torch.tensor([1.0, 1.0], dtype=torch.float)

        data = Data(x=x, pos=pos, edge_index=edge_index, edge_attr=edge_attr)

        output = model(data)
        loss = output.sum()
        loss.backward()

        # Check that parameters have gradients
        has_grad = False
        for param in model.parameters():
            if param.grad is not None:
                has_grad = True
                break
        
        assert has_grad, "No gradients computed for model parameters"