"""
Unit tests for the Spectral GNN architecture.

Tests verify:
1. Model initialization with various configurations.
2. Forward pass produces valid outputs.
3. CPU-only execution (no CUDA usage).
4. Gradient computation works correctly.
"""

import pytest
import torch
import os
import sys

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models.spectral_gnn import SpectralGNN, get_spectral_gnn_model


class TestSpectralGNNInitialization:
    """Tests for model initialization."""

    def test_default_initialization(self):
        """Test model initializes with default parameters."""
        model = SpectralGNN(node_input_dim=10)
        assert model.node_input_dim == 10
        assert model.hidden_dim == 64
        assert model.output_dim == 1
        assert model.num_layers == 2
        assert model.dropout_rate == 0.1

    def test_custom_initialization(self):
        """Test model initializes with custom parameters."""
        model = SpectralGNN(
            node_input_dim=20,
            hidden_dim=128,
            output_dim=3,
            dropout_rate=0.5,
            num_layers=3
        )
        assert model.node_input_dim == 20
        assert model.hidden_dim == 128
        assert model.output_dim == 3
        assert model.num_layers == 3
        assert model.dropout_rate == 0.5

    def test_factory_function(self):
        """Test factory function creates model correctly."""
        model = get_spectral_gnn_model()
        assert isinstance(model, SpectralGNN)
        assert model.node_input_dim == 10  # Default from config


class TestSpectralGNNForward:
    """Tests for forward pass."""

    def test_single_graph_forward(self):
        """Test forward pass with a single graph."""
        model = SpectralGNN(node_input_dim=10)
        model.eval()

        num_nodes = 10
        num_edges = 20
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        batch = torch.zeros(num_nodes, dtype=torch.long)

        with torch.no_grad():
            output = model(x, edge_index, batch=batch)

        assert output.shape == (1, 1), f"Expected shape (1, 1), got {output.shape}"
        assert not torch.isnan(output).any(), "Output contains NaN values"
        assert not torch.isinf(output).any(), "Output contains Inf values"

    def test_batched_graphs_forward(self):
        """Test forward pass with multiple graphs in a batch."""
        model = SpectralGNN(node_input_dim=10)
        model.eval()

        num_graphs = 3
        num_nodes_per_graph = 10
        total_nodes = num_graphs * num_nodes_per_graph
        num_edges = 20

        x = torch.randn(total_nodes, 10)
        edge_index = torch.randint(0, num_nodes_per_graph, (2, num_edges))
        # Adjust edge_index for each graph
        for i in range(1, num_graphs):
            offset = i * num_nodes_per_graph
            edge_index[:, (i-1)*num_edges:i*num_edges] += offset

        batch = torch.repeat_interleave(torch.arange(num_graphs), num_nodes_per_graph)

        with torch.no_grad():
            output = model(x, edge_index, batch=batch)

        assert output.shape == (num_graphs, 1), f"Expected shape ({num_graphs}, 1), got {output.shape}"
        assert not torch.isnan(output).any(), "Output contains NaN values"

    def test_forward_with_gradients(self):
        """Test that gradients flow correctly through the model."""
        model = SpectralGNN(node_input_dim=10)
        model.train()

        num_nodes = 10
        num_edges = 20
        x = torch.randn(num_nodes, 10, requires_grad=True)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        batch = torch.zeros(num_nodes, dtype=torch.long)

        output = model(x, edge_index, batch=batch)
        loss = output.sum()
        loss.backward()

        assert x.grad is not None, "Gradients did not flow to input"
        assert not torch.isnan(x.grad).any(), "Gradients contain NaN values"


class TestSpectralGNNEngineering:
    """Tests for engineering constraints."""

    def test_cpu_only_execution(self):
        """Verify model runs on CPU without CUDA."""
        model = SpectralGNN(node_input_dim=10)
        assert next(model.parameters()).device.type == "cpu", "Model parameters not on CPU"

        num_nodes = 10
        num_edges = 20
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        batch = torch.zeros(num_nodes, dtype=torch.long)

        # Force CPU
        model = model.cpu()
        x = x.cpu()
        edge_index = edge_index.cpu()
        batch = batch.cpu()

        model.eval()
        with torch.no_grad():
            output = model(x, edge_index, batch=batch)

        assert output.device.type == "cpu", "Output not on CPU"

    def test_reset_parameters(self):
        """Test parameter reset functionality."""
        model = SpectralGNN(node_input_dim=10)
        initial_weight = model.fc1.weight.clone()

        model.reset_parameters()

        assert not torch.equal(model.fc1.weight, initial_weight), "Parameters not reset"

    def test_model_size(self):
        """Test model has reasonable size for lightweight requirement."""
        model = SpectralGNN(node_input_dim=10)
        param_count = sum(p.numel() for p in model.parameters())
        assert param_count < 100000, f"Model too large: {param_count} parameters"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])