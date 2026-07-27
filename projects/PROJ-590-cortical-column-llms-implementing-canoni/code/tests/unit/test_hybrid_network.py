"""
Unit tests for HybridNetwork.

Tests:
- test_forward_pass_cpu: Instantiates the model and asserts no shape mismatches.
- test_parameter_count_parity: Checks that parameter count is within ±1% of baseline.
- test_microcircuit_integration: Verifies that the microcircuit module is correctly integrated.
"""

import pytest
import torch
import torch.nn as nn
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.models.hybrid_network import HybridNetwork, create_hybrid_network, HybridAttentionBlock
from src.models.baseline_transformer import BaselineTransformerLayer  # Assuming this exists


class TestHybridNetwork:
    """Test suite for HybridNetwork."""

    def test_forward_pass_cpu(self):
        """Test that forward pass works on CPU without shape mismatches."""
        # Create model
        model = create_hybrid_network(
            d_model=128,
            nhead=4,
            num_layers=2,
            dim_feedforward=256,
            input_dim=784,
            output_dim=10,
            microcircuit_neurons=32,
            microcircuit_layers=2,
        )

        # Create dummy input
        batch_size = 2
        seq_len = 10
        x = torch.randn(batch_size, seq_len, 784)

        # Forward pass
        output = model(x)

        # Assert output shape
        assert output.shape == (batch_size, 10), f"Expected output shape (batch, 10), got {output.shape}"

    def test_parameter_count_parity(self):
        """Test that parameter count is within ±1% of a standard Transformer."""
        # Create hybrid model
        hybrid_model = create_hybrid_network(
            d_model=128,
            nhead=4,
            num_layers=2,
            dim_feedforward=256,
            input_dim=784,
            output_dim=10,
            microcircuit_neurons=32,
            microcircuit_layers=2,
        )

        # Create a standard transformer-like model for comparison
        # (We approximate the baseline structure)
        class BaselineSimple(nn.Module):
            def __init__(self, d_model, nhead, num_layers, dim_feedforward, input_dim, output_dim):
                super().__init__()
                self.input_proj = nn.Linear(input_dim, d_model)
                self.pos_encoder = nn.Parameter(torch.randn(1, 10, d_model))  # Fixed pos
                self.layers = nn.ModuleList([
                    nn.TransformerEncoderLayer(
                        d_model=d_model,
                        nhead=nhead,
                        dim_feedforward=dim_feedforward,
                        dropout=0.1,
                        batch_first=True,
                    )
                    for _ in range(num_layers)
                ])
                self.output_proj = nn.Linear(d_model, output_dim)

            def forward(self, x):
                if x.dim() == 2:
                    x = x.unsqueeze(1)
                x = self.input_proj(x)
                x = x + self.pos_encoder[:, :x.size(1), :]
                for layer in self.layers:
                    x = layer(x)
                x = x.mean(dim=1)
                return self.output_proj(x)

        baseline_model = BaselineSimple(
            d_model=128,
            nhead=4,
            num_layers=2,
            dim_feedforward=256,
            input_dim=784,
            output_dim=10,
        )

        hybrid_params = hybrid_model.count_parameters()
        baseline_params = sum(p.numel() for p in baseline_model.parameters())

        # Check parity (±1%)
        ratio = hybrid_params / baseline_params
        assert 0.99 <= ratio <= 1.01, f"Parameter count mismatch: {hybrid_params} vs {baseline_params} (ratio={ratio:.4f})"

    def test_microcircuit_integration(self):
        """Test that the microcircuit module is correctly integrated."""
        model = create_hybrid_network(
            d_model=64,
            nhead=2,
            num_layers=1,
            dim_feedforward=128,
            input_dim=784,
            output_dim=5,
            microcircuit_neurons=16,
            microcircuit_layers=2,
        )

        # Check that the microcircuit exists in the block
        block = model.blocks[0]
        assert hasattr(block, "microcircuit"), "Block does not have a microcircuit attribute"

        # Check that the microcircuit is a module
        assert isinstance(block.microcircuit, nn.Module), "microcircuit is not a nn.Module"

        # Check that the microcircuit can be called
        dummy_input = torch.randn(1, 5, 64)
        output = block.microcircuit(dummy_input)
        assert output.shape == (1, 5, 64), f"Microcircuit output shape mismatch: {output.shape}"

    def test_attention_mask_handling(self):
        """Test that attention masks are correctly passed through."""
        model = create_hybrid_network(
            d_model=64,
            nhead=2,
            num_layers=1,
            dim_feedforward=128,
            input_dim=784,
            output_dim=5,
            microcircuit_neurons=16,
            microcircuit_layers=2,
        )

        batch_size = 2
        seq_len = 10
        x = torch.randn(batch_size, seq_len, 784)

        # Create a simple attention mask (no masking)
        mask = torch.ones(seq_len, seq_len)  # (seq_len, seq_len)

        # Forward pass with mask
        output = model(x, src_mask=mask)
        assert output.shape == (batch_size, 5)

    def test_key_padding_mask_handling(self):
        """Test that key padding masks are correctly passed through."""
        model = create_hybrid_network(
            d_model=64,
            nhead=2,
            num_layers=1,
            dim_feedforward=128,
            input_dim=784,
            output_dim=5,
            microcircuit_neurons=16,
            microcircuit_layers=2,
        )

        batch_size = 2
        seq_len = 10
        x = torch.randn(batch_size, seq_len, 784)

        # Create a key padding mask (0 = valid, 1 = padded)
        key_padding_mask = torch.zeros(batch_size, seq_len, dtype=torch.bool)

        # Forward pass with key padding mask
        output = model(x, src_key_padding_mask=key_padding_mask)
        assert output.shape == (batch_size, 5)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])