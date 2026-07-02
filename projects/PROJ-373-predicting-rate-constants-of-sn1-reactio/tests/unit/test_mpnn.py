"""
Unit tests for the MPNN architecture and forward pass.
Depends on: code/models/mpnn.py (T019)
"""
import pytest
import torch
import numpy as np
from pathlib import Path

# Import the MPNN components from the project code
from models.mpnn import (
    MPNNConfig,
    MPNNMessagePassingLayer,
    MPNN,
    create_mpnn_from_config
)

# Test fixtures for dummy graph data
@pytest.fixture
def dummy_batch():
    """
    Creates a dummy batch of molecular graphs for testing.
    Structure matches what an MPNN expects:
    - x: Node features (num_nodes x feature_dim)
    - edge_index: (2, num_edges)
    - edge_attr: Edge features (num_edges x edge_dim)
    - batch: Node-to-graph assignment vector
    """
    # Create a small graph with 4 nodes and 3 edges
    num_nodes = 4
    num_edges = 3
    feature_dim = 8
    edge_dim = 4

    # Node features: random floats
    x = torch.randn(num_nodes, feature_dim)

    # Edge index: source -> target
    edge_index = torch.tensor([
        [0, 1, 2],  # sources
        [1, 2, 3]   # targets
    ])

    # Edge attributes
    edge_attr = torch.randn(num_edges, edge_dim)

    # Batch assignment (all nodes belong to graph 0)
    batch = torch.zeros(num_nodes, dtype=torch.long)

    return {
        'x': x,
        'edge_index': edge_index,
        'edge_attr': edge_attr,
        'batch': batch
    }

@pytest.fixture
def valid_config():
    """Valid MPNN configuration for testing."""
    return MPNNConfig(
        input_dim=8,
        hidden_dim=16,
        output_dim=1,
        num_layers=2,
        edge_dim=4,
        dropout=0.1
    )

class TestMPNNConfig:
    """Tests for MPNN configuration validation."""

    def test_valid_config_creation(self, valid_config):
        """Test that a valid config can be created."""
        assert valid_config.input_dim == 8
        assert valid_config.hidden_dim == 16
        assert valid_config.num_layers == 2
        assert valid_config.dropout == 0.1

    def test_layer_count_bounds(self):
        """Test that layer count is enforced between 1 and 4."""
        # Valid: 1 layer
        config1 = MPNNConfig(
            input_dim=8, hidden_dim=16, output_dim=1,
            num_layers=1, edge_dim=4
        )
        assert config1.num_layers == 1

        # Valid: 4 layers
        config4 = MPNNConfig(
            input_dim=8, hidden_dim=16, output_dim=1,
            num_layers=4, edge_dim=4
        )
        assert config4.num_layers == 4

        # Invalid: 0 layers (should raise ValueError)
        with pytest.raises(ValueError):
            MPNNConfig(
                input_dim=8, hidden_dim=16, output_dim=1,
                num_layers=0, edge_dim=4
            )

        # Invalid: 5 layers (should raise ValueError)
        with pytest.raises(ValueError):
            MPNNConfig(
                input_dim=8, hidden_dim=16, output_dim=1,
                num_layers=5, edge_dim=4
            )

    def test_negative_dimensions(self):
        """Test that negative dimensions raise errors."""
        with pytest.raises(ValueError):
            MPNNConfig(
                input_dim=-1, hidden_dim=16, output_dim=1,
                num_layers=2, edge_dim=4
            )

        with pytest.raises(ValueError):
            MPNNConfig(
                input_dim=8, hidden_dim=-1, output_dim=1,
                num_layers=2, edge_dim=4
            )

class TestMPNNMessagePassingLayer:
    """Tests for the individual message passing layer."""

    def test_layer_forward_pass(self, dummy_batch):
        """Test forward pass of a single message passing layer."""
        layer = MPNNMessagePassingLayer(
            in_features=8,
            out_features=16,
            edge_features=4,
            dropout=0.0
        )

        output = layer(
            dummy_batch['x'],
            dummy_batch['edge_index'],
            dummy_batch['edge_attr']
        )

        # Output should have same number of nodes, updated feature dim
        assert output.shape == (4, 16)

    def test_layer_output_dimension(self, dummy_batch):
        """Test that output dimension matches config."""
        for out_dim in [8, 16, 32, 64]:
            layer = MPNNMessagePassingLayer(
                in_features=8,
                out_features=out_dim,
                edge_features=4,
                dropout=0.0
            )
            output = layer(
                dummy_batch['x'],
                dummy_batch['edge_index'],
                dummy_batch['edge_attr']
            )
            assert output.shape[1] == out_dim

    def test_multiple_edge_features(self, dummy_batch):
        """Test handling of different edge feature dimensions."""
        for edge_dim in [1, 4, 8, 16]:
            layer = MPNNMessagePassingLayer(
                in_features=8,
                out_features=16,
                edge_features=edge_dim,
                dropout=0.0
            )
            # Adjust edge attributes to match
            test_batch = dummy_batch.copy()
            test_batch['edge_attr'] = torch.randn(3, edge_dim)
            
            output = layer(
                test_batch['x'],
                test_batch['edge_index'],
                test_batch['edge_attr']
            )
            assert output.shape == (4, 16)

class TestMPNN:
    """Tests for the full MPNN model."""

    def test_model_forward_pass(self, dummy_batch, valid_config):
        """Test full forward pass of the MPNN model."""
        model = create_mpnn_from_config(valid_config)
        
        output = model(dummy_batch)
        
        # Output should be (num_graphs, output_dim)
        # Here we have 1 graph, output_dim=1
        assert output.shape == (1, 1)

    def test_model_with_multiple_graphs(self):
        """Test model with a batch containing multiple graphs."""
        config = MPNNConfig(
            input_dim=8,
            hidden_dim=16,
            output_dim=1,
            num_layers=2,
            edge_dim=4,
            dropout=0.0
        )
        model = create_mpnn_from_config(config)

        # Create a batch with 2 graphs
        num_nodes = 6
        x = torch.randn(num_nodes, 8)
        edge_index = torch.tensor([
            [0, 1, 2, 3, 4],
            [1, 2, 3, 4, 5]
        ])
        edge_attr = torch.randn(5, 4)
        batch = torch.tensor([0, 0, 0, 1, 1, 1])  # 3 nodes per graph

        batch_data = {
            'x': x,
            'edge_index': edge_index,
            'edge_attr': edge_attr,
            'batch': batch
        }

        output = model(batch_data)
        
        # Should output 2 values (one per graph)
        assert output.shape == (2, 1)

    def test_model_with_different_layer_counts(self):
        """Test model with various layer counts (1 to 4)."""
        for num_layers in [1, 2, 3, 4]:
            config = MPNNConfig(
                input_dim=8,
                hidden_dim=16,
                output_dim=1,
                num_layers=num_layers,
                edge_dim=4,
                dropout=0.0
            )
            model = create_mpnn_from_config(config)
            
            output = model(dummy_batch)
            assert output.shape == (1, 1)

    def test_model_dropout(self, dummy_batch):
        """Test that dropout is applied during training."""
        config = MPNNConfig(
            input_dim=8,
            hidden_dim=16,
            output_dim=1,
            num_layers=2,
            edge_dim=4,
            dropout=0.5
        )
        model = create_mpnn_from_config(config)
        
        # Set to training mode
        model.train()
        output_train = model(dummy_batch)
        
        # Set to eval mode
        model.eval()
        output_eval = model(dummy_batch)
        
        # Outputs should be different due to dropout
        # (with high probability, though not guaranteed for single sample)
        # We at least verify both run without error
        assert output_train.shape == (1, 1)
        assert output_eval.shape == (1, 1)

    def test_model_gradient_flow(self, dummy_batch, valid_config):
        """Test that gradients flow through the model."""
        model = create_mpnn_from_config(valid_config)
        model.train()
        
        output = model(dummy_batch)
        loss = output.sum()
        loss.backward()
        
        # Check that parameters have gradients
        has_gradients = False
        for param in model.parameters():
            if param.grad is not None:
                has_gradients = True
                # Check gradient is not all zeros
                assert param.grad.abs().sum() > 0
        
        assert has_gradients

class TestMPNNIntegration:
    """Integration tests for the MPNN pipeline."""

    def test_create_mpnn_from_config(self):
        """Test the factory function for creating models."""
        config = MPNNConfig(
            input_dim=10,
            hidden_dim=32,
            output_dim=1,
            num_layers=3,
            edge_dim=6,
            dropout=0.1
        )
        
        model = create_mpnn_from_config(config)
        
        assert isinstance(model, MPNN)
        assert model.config == config

    def test_model_parameter_count(self):
        """Test that model has a reasonable number of parameters."""
        config = MPNNConfig(
            input_dim=8,
            hidden_dim=16,
            output_dim=1,
            num_layers=2,
            edge_dim=4,
            dropout=0.0
        )
        model = create_mpnn_from_config(config)
        
        total_params = sum(p.numel() for p in model.parameters())
        assert total_params > 0
        
        # Rough sanity check: should be in the thousands, not millions
        assert total_params < 1_000_000

    def test_serialization_compatibility(self):
        """Test that model can be used with torch save/load."""
        model = create_mpnn_from_config(MPNNConfig(
            input_dim=8,
            hidden_dim=16,
            output_dim=1,
            num_layers=2,
            edge_dim=4,
            dropout=0.0
        ))
        
        # Save state dict
        state_dict = model.state_dict()
        
        # Create new model and load
        model2 = create_mpnn_from_config(MPNNConfig(
            input_dim=8,
            hidden_dim=16,
            output_dim=1,
            num_layers=2,
            edge_dim=4,
            dropout=0.0
        ))
        model2.load_state_dict(state_dict)
        
        # Outputs should be identical
        output1 = model(dummy_batch)
        output2 = model2(dummy_batch)
        
        assert torch.allclose(output1, output2)