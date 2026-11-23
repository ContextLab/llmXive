"""Integration tests for model components working together."""

import pytest
import torch
import torch.nn as nn
from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.training.homeostasis import HomeostaticScaler, apply_scaling_hook

class TestMicrocircuitColumnIntegration:
    def test_column_forward_pass(self):
        """Test full forward pass through a microcircuit column."""
        column = create_microcircuit_column(hidden_dim=64, neurons_per_layer=128)
        batch_size = 4
        seq_len = 10

        x = torch.randn(batch_size, seq_len, 64)
        output = column(x)

        assert output.shape[0] == batch_size
        assert output.shape[1] == seq_len
        assert output.shape[2] == 64

    def test_column_with_different_sizes(self):
        """Test column with various input sizes."""
        column = create_microcircuit_column(hidden_dim=32, neurons_per_layer=64)

        for batch_size in [1, 2, 8]:
            for seq_len in [5, 15, 30]:
                x = torch.randn(batch_size, seq_len, 32)
                output = column(x)
                assert output.shape == (batch_size, seq_len, 32)

class TestHybridNetworkIntegration:
    def test_hybrid_network_forward(self):
        """Test forward pass through hybrid network."""
        model = create_hybrid_network(hidden_dim=64, num_layers=2)
        batch_size = 2
        seq_len = 8

        x = torch.randn(batch_size, seq_len, 64)
        output = model(x)

        assert output.shape[0] == batch_size
        assert output.shape[1] == seq_len

    def test_hybrid_network_parameter_count(self):
        """Test that hybrid network has reasonable parameter count."""
        model = create_hybrid_network(hidden_dim=64, num_layers=2)
        total_params = sum(p.numel() for p in model.parameters())
        assert total_params > 0
        # Should be in a reasonable range for a small model
        assert 1000 < total_params < 1000000

class TestHomeostasisIntegration:
    def test_homeostatic_scaler_integration(self):
        """Test homeostatic scaler works with a model."""
        model = create_hybrid_network(hidden_dim=32, num_layers=1)
        scaler = HomeostaticScaler(target_ratio=4.0, decay_rate=0.01)

        # Simulate a training step
        x = torch.randn(2, 5, 32)
        output = model(x)
        loss = output.sum()
        loss.backward()

        # Apply scaling hook
        scaling_info = apply_scaling_hook(model, step=1, homeostatic_scaler=scaler)

        assert 'scaling_factor' in scaling_info
        assert isinstance(scaling_info['scaling_factor'], float)

    def test_scaling_preserves_shapes(self):
        """Test that scaling doesn't change tensor shapes."""
        model = create_hybrid_network(hidden_dim=32, num_layers=1)
        scaler = HomeostaticScaler(target_ratio=4.0, decay_rate=0.01)

        x = torch.randn(2, 5, 32)
        output_before = model(x)

        # Apply scaling
        apply_scaling_hook(model, step=1, homeostatic_scaler=scaler)

        output_after = model(x)

        assert output_before.shape == output_after.shape
