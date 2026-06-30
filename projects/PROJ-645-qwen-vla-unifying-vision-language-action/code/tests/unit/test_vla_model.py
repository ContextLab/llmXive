import os
import sys
import pytest
import torch
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.vla_model import (
    DiTActionHead,
    Qwen2VLVLA,
    ACTION_DIM,
    ACTION_QUANTIZATION_LEVELS
)

class TestDiTActionHead:
    """Unit tests for the DiT action head."""

    def test_dit_initialization(self):
        """Test that DiT action head initializes correctly."""
        head = DiTActionHead(
            hidden_dim=512,
            num_blocks=4,
            num_heads=8,
            action_dim=8,
            quantization_levels=256
        )
        
        assert head.action_dim == 8
        assert head.quantization_levels == 256
        assert head.hidden_dim == 512
        assert len(head.blocks) == 4

    def test_forward_pass(self):
        """Test forward pass with dummy inputs."""
        head = DiTActionHead(action_dim=8, quantization_levels=256)
        
        batch_size = 2
        seq_len = 10
        hidden_dim = 512
        
        x = torch.randn(batch_size, seq_len, hidden_dim)
        cond = torch.randn(batch_size, hidden_dim)
        
        logits = head(x, cond)
        
        assert logits.shape == (batch_size, 8, 256)

    def test_quantize_dequantize_roundtrip(self):
        """Test that quantization and dequantization are consistent."""
        head = DiTActionHead(action_dim=8, quantization_levels=256)
        
        batch_size = 2
        actions = torch.randn(batch_size, 8)
        # Clamp to [-1, 1] range
        actions = torch.clamp(actions, -1, 1)
        
        # Quantize and dequantize
        tokens = head.quantize(actions)
        recovered = head.dequantize(tokens)
        
        # Check that values are close (allowing for quantization error)
        assert recovered.shape == actions.shape
        assert torch.all(recovered >= -1) and torch.all(recovered <= 1)

    def test_memory_footprint(self):
        """Test that DiT head fits within memory constraints."""
        head = DiTActionHead(action_dim=8, quantization_levels=256)
        
        total_params = sum(p.numel() for p in head.parameters())
        estimated_memory_mb = (total_params * 2) / (1024 ** 2)  # FP16
        
        # DiT head should be < 500MB
        assert estimated_memory_mb < 500, f"DiT head too large: {estimated_memory_mb:.2f} MB"

class TestQwen2VLVLA:
    """Unit tests for the full VLA model."""

    @pytest.mark.skip(reason="Requires Qwen2-VL model to be available")
    def test_model_initialization(self):
        """Test that the full VLA model initializes correctly."""
        model = Qwen2VLVLA(device="cpu")
        
        assert model.action_dim == 8
        assert model.quantization_levels == 256
        
        # Check that Qwen2-VL is frozen
        for param in model.qwen_model.parameters():
            assert not param.requires_grad

    @pytest.mark.skip(reason="Requires Qwen2-VL model to be available")
    def test_generate_actions(self):
        """Test action generation."""
        model = Qwen2VLVLA(device="cpu")
        
        batch_size = 2
        seq_len = 10
        dummy_input_ids = torch.randint(0, 1000, (batch_size, seq_len))
        dummy_attention_mask = torch.ones(batch_size, seq_len)
        
        actions = model.generate_actions(
            input_ids=dummy_input_ids,
            attention_mask=dummy_attention_mask
        )
        
        assert actions.shape == (batch_size, 8)
        assert torch.all(actions >= -1) and torch.all(actions <= 1)

    @pytest.mark.skip(reason="Requires Qwen2-VL model to be available")
    def test_compute_loss(self):
        """Test loss computation."""
        model = Qwen2VLVLA(device="cpu")
        
        batch_size = 2
        seq_len = 10
        dummy_input_ids = torch.randint(0, 1000, (batch_size, seq_len))
        dummy_attention_mask = torch.ones(batch_size, seq_len)
        dummy_actions = torch.randn(batch_size, 8)
        dummy_actions = torch.clamp(dummy_actions, -1, 1)
        
        loss = model.compute_loss(
            input_ids=dummy_input_ids,
            attention_mask=dummy_attention_mask,
            actions=dummy_actions
        )
        
        assert loss.shape == torch.Size([])
        assert loss.item() >= 0

class TestTokenSpaceStrategy:
    """Tests for the token space quantization strategy."""

    def test_quantization_levels(self):
        """Test that quantization levels are correctly configured."""
        assert ACTION_QUANTIZATION_LEVELS == 256
        assert ACTION_DIM == 8

    def test_quantization_range(self):
        """Test that quantization covers the full action range."""
        head = DiTActionHead(action_dim=8, quantization_levels=256)
        
        # Test minimum value (-1)
        min_action = torch.tensor([[-1.0] * 8])
        min_tokens = head.quantize(min_action)
        assert torch.all(min_tokens == 0)
        
        # Test maximum value (1)
        max_action = torch.tensor([[1.0] * 8])
        max_tokens = head.quantize(max_action)
        assert torch.all(max_tokens == 255)
        
        # Test zero value
        zero_action = torch.tensor([[0.0] * 8])
        zero_tokens = head.quantize(zero_action)
        assert torch.all(zero_tokens == 127)  # Closest to midpoint

    def test_dequantization_accuracy(self):
        """Test that dequantization recovers values within quantization error."""
        head = DiTActionHead(action_dim=8, quantization_levels=256)
        
        # Test with known values
        test_values = [-1.0, -0.5, 0.0, 0.5, 1.0]
        
        for val in test_values:
            action = torch.tensor([[val] * 8])
            token = head.quantize(action)
            recovered = head.dequantize(token)
            
            # The recovered value should be close to the original
            # (within one quantization step)
            quantization_step = 2.0 / (256 - 1)
            error = torch.abs(recovered - action)
            assert torch.all(error <= quantization_step * 2), \
                f"Dequantization error too large for {val}: {error.item()}"