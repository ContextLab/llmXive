"""
Unit tests for the BaselineTransformer implementation.

These tests verify the correct construction and forward pass behavior
of the standard Transformer architecture.
"""

import pytest
import torch
import torch.nn as nn

from src.models.baseline_transformer import (
    BaselineTransformer,
    MultiHeadAttention,
    FeedForward,
    TransformerBlock,
    create_baseline_transformer
)


class TestFeedForward:
    """Tests for the FeedForward (MLP) layer."""

    def test_feedforward_forward_pass(self):
        """Test basic forward pass of FeedForward layer."""
        d_model = 128
        d_ff = 512
        batch_size = 4
        seq_len = 10

        ff = FeedForward(d_model, d_ff)
        x = torch.randn(batch_size, seq_len, d_model)

        output = ff(x)

        assert output.shape == (batch_size, seq_len, d_model)
        assert not torch.isnan(output).any()

    def test_feedforward_dropout(self):
        """Test that dropout is applied during training."""
        d_model = 128
        d_ff = 512
        ff = FeedForward(d_model, d_ff, dropout=0.5)
        ff.train()

        x = torch.ones(1, 1, d_model)
        output = ff(x)

        # With dropout, output should not be exactly ones
        assert not torch.allclose(output, x)


class TestMultiHeadAttention:
    """Tests for the MultiHeadAttention layer."""

    def test_attention_forward_pass(self):
        """Test basic forward pass of attention layer."""
        d_model = 128
        n_heads = 4
        batch_size = 2
        seq_len = 16

        attn = MultiHeadAttention(d_model, n_heads)
        x = torch.randn(batch_size, seq_len, d_model)

        output = attn(x, x, x)

        assert output.shape == (batch_size, seq_len, d_model)
        assert not torch.isnan(output).any()

    def test_attention_with_mask(self):
        """Test attention with padding mask."""
        d_model = 128
        n_heads = 4
        batch_size = 2
        seq_len = 16

        attn = MultiHeadAttention(d_model, n_heads)
        x = torch.randn(batch_size, seq_len, d_model)

        # Create mask: first 8 positions valid, last 8 invalid
        mask = torch.ones(batch_size, seq_len, seq_len)
        mask[:, :, 8:] = 0

        output = attn(x, x, x, mask)

        assert output.shape == (batch_size, seq_len, d_model)

    def test_attention_different_kv(self):
        """Test attention with different key/value tensors."""
        d_model = 128
        n_heads = 4
        batch_size = 2
        query_len = 8
        kv_len = 16

        attn = MultiHeadAttention(d_model, n_heads)
        query = torch.randn(batch_size, query_len, d_model)
        key = torch.randn(batch_size, kv_len, d_model)
        value = torch.randn(batch_size, kv_len, d_model)

        output = attn(query, key, value)

        assert output.shape == (batch_size, query_len, d_model)


class TestTransformerBlock:
    """Tests for the full Transformer block."""

    def test_transformer_block_forward(self):
        """Test forward pass of a complete Transformer block."""
        d_model = 128
        n_heads = 4
        d_ff = 512
        batch_size = 2
        seq_len = 16

        block = TransformerBlock(d_model, n_heads, d_ff)
        x = torch.randn(batch_size, seq_len, d_model)

        output = block(x)

        assert output.shape == (batch_size, seq_len, d_model)
        assert not torch.isnan(output).any()

    def test_transformer_block_residual(self):
        """Test that residual connections preserve information."""
        d_model = 128
        n_heads = 4
        d_ff = 512

        block = TransformerBlock(d_model, n_heads, d_ff, dropout=0.0)
        x = torch.randn(1, 1, d_model)

        output = block(x)

        # With zero dropout and small weights, output should be similar to input
        # (not identical due to layer norms and activations)
        assert torch.allclose(output, x, atol=1.0)


class TestBaselineTransformer:
    """Tests for the complete BaselineTransformer model."""

    def test_model_initialization(self):
        """Test that model initializes correctly."""
        model = create_baseline_transformer(
            d_model=128,
            n_heads=4,
            n_layers=2,
            d_ff=512,
            input_dim=256,
            output_dim=256
        )

        assert isinstance(model, BaselineTransformer)
        assert model.d_model == 128
        assert model.n_heads == 4
        assert model.n_layers == 2

    def test_model_forward_pass(self):
        """Test complete forward pass through the model."""
        model = create_baseline_transformer(
            d_model=128,
            n_heads=4,
            n_layers=2,
            d_ff=512,
            input_dim=256,
            output_dim=256,
            max_seq_len=32
        )

        batch_size = 2
        seq_len = 16
        x = torch.randn(batch_size, seq_len, 256)

        output = model(x)

        assert output.shape == (batch_size, seq_len, 256)
        assert not torch.isnan(output).any()

    def test_model_with_mask(self):
        """Test model with attention mask."""
        model = create_baseline_transformer(
            d_model=128,
            n_heads=4,
            n_layers=2,
            d_ff=512,
            input_dim=256,
            output_dim=256,
            max_seq_len=32
        )

        batch_size = 2
        seq_len = 16
        x = torch.randn(batch_size, seq_len, 256)

        # Create causal mask
        mask = torch.tril(torch.ones(seq_len, seq_len)).unsqueeze(0).unsqueeze(0)
        mask = mask.expand(batch_size, 1, seq_len, seq_len)

        output = model(x, mask)

        assert output.shape == (batch_size, seq_len, 256)

    def test_parameter_count(self):
        """Test that parameter counting methods work."""
        model = create_baseline_transformer(
            d_model=128,
            n_heads=4,
            n_layers=2,
            d_ff=512,
            input_dim=256,
            output_dim=256
        )

        total_params = model.get_num_parameters()
        trainable_params = model.get_num_trainable_parameters()

        assert total_params > 0
        assert trainable_params == total_params  # All params are trainable by default

    def test_model_size_variations(self):
        """Test model with different size configurations."""
        configs = [
            {"d_model": 64, "n_heads": 2, "n_layers": 1, "d_ff": 256},
            {"d_model": 256, "n_heads": 8, "n_layers": 4, "d_ff": 1024},
            {"d_model": 512, "n_heads": 16, "n_layers": 8, "d_ff": 2048},
        ]

        for config in configs:
            model = create_baseline_transformer(
                **config,
                input_dim=128,
                output_dim=128
            )

            x = torch.randn(1, 8, 128)
            output = model(x)

            assert output.shape == (1, 8, 128)

    def test_gradient_flow(self):
        """Test that gradients flow through the model."""
        model = create_baseline_transformer(
            d_model=64,
            n_heads=2,
            n_layers=1,
            d_ff=256,
            input_dim=128,
            output_dim=128
        )

        x = torch.randn(2, 8, 128, requires_grad=True)
        output = model(x)
        loss = output.sum()
        loss.backward()

        assert x.grad is not None
        assert not torch.isnan(x.grad).any()
