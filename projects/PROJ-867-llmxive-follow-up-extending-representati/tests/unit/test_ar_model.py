"""
tests/unit/test_ar_model.py

Unit tests for the LightweightAutoregressiveModel.
"""
import pytest
import torch
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.autoregressive import (
    LightweightAutoregressiveModel,
    get_default_config,
    create_ar_model
)


class TestLightweightAutoregressiveModel:
    """Test suite for LightweightAutoregressiveModel."""

    def test_model_initialization(self):
        """Test that the model initializes correctly with default config."""
        model = create_ar_model()
        
        assert isinstance(model, LightweightAutoregressiveModel)
        assert model.model_dim == 256
        assert model.vocab_size == 30522
        assert model.max_seq_len == 512
        
        # Check that required components exist
        assert hasattr(model, 'input_projection')
        assert hasattr(model, 'pos_embedding')
        assert hasattr(model, 'transformer_decoder')
        assert hasattr(model, 'output_projection')

    def test_forward_pass_inference(self):
        """Test forward pass in inference mode."""
        model = create_ar_model()
        model.eval()
        
        batch_size = 2
        seq_len = 10
        input_dim = 768
        
        rf_tokens = torch.randn(batch_size, seq_len, input_dim)
        
        with torch.no_grad():
            logits, loss = model(rf_tokens)
        
        assert logits.shape == (batch_size, seq_len + 1, model.vocab_size)
        assert loss is None

    def test_forward_pass_training(self):
        """Test forward pass in training mode with target tokens."""
        model = create_ar_model()
        model.train()
        
        batch_size = 2
        seq_len = 10
        input_dim = 768
        
        rf_tokens = torch.randn(batch_size, seq_len, input_dim)
        target_tokens = torch.randint(0, 30522, (batch_size, seq_len))
        
        logits, loss = model(rf_tokens, target_tokens)
        
        assert logits.shape == (batch_size, seq_len + 1, model.vocab_size)
        assert loss is not None
        assert isinstance(loss, torch.Tensor)
        assert loss.requires_grad

    def test_gradient_flow(self):
        """Test that gradients flow through the model."""
        model = create_ar_model()
        model.train()
        
        batch_size = 2
        seq_len = 10
        input_dim = 768
        
        rf_tokens = torch.randn(batch_size, seq_len, input_dim, requires_grad=True)
        target_tokens = torch.randint(0, 30522, (batch_size, seq_len))
        
        logits, loss = model(rf_tokens, target_tokens)
        
        # Backward pass
        loss.backward()
        
        # Check that gradients exist for model parameters
        for name, param in model.named_parameters():
            assert param.grad is not None, f"No gradient for {name}"
            assert param.grad.shape == param.shape

    def test_generation(self):
        """Test autoregressive generation."""
        model = create_ar_model()
        model.eval()
        
        batch_size = 1
        seq_len = 5
        input_dim = 768
        
        rf_tokens = torch.randn(batch_size, seq_len, input_dim)
        
        with torch.no_grad():
            generated = model.generate(rf_tokens, max_length=10)
        
        assert isinstance(generated, list)
        assert len(generated) == batch_size
        assert isinstance(generated[0], list)
        assert len(generated[0]) > 0

    def test_config_defaults(self):
        """Test that default config returns expected values."""
        config = get_default_config()
        
        assert 'input_dim' in config
        assert 'model_dim' in config
        assert 'num_heads' in config
        assert 'num_layers' in config
        assert 'vocab_size' in config
        assert 'max_seq_len' in config
        assert 'dropout' in config

    def test_custom_config(self):
        """Test model creation with custom configuration."""
        custom_config = {
            'input_dim': 512,
            'model_dim': 128,
            'num_heads': 2,
            'num_layers': 2,
            'vocab_size': 1000,
            'max_seq_len': 256,
            'dropout': 0.2
        }
        
        model = create_ar_model(custom_config)
        
        assert model.model_dim == 128
        assert model.num_heads == 2
        assert model.vocab_size == 1000
        assert model.max_seq_len == 256

    def test_memory_efficiency(self):
        """Test that model parameters fit within reasonable memory bounds."""
        model = create_ar_model()
        
        # Count total parameters
        total_params = sum(p.numel() for p in model.parameters())
        
        # For a lightweight model, should be < 10M parameters
        assert total_params < 10_000_000, f"Model has too many parameters: {total_params}"
        
        # Estimate memory usage (4 bytes per float)
        memory_mb = (total_params * 4) / (1024 * 1024)
        assert memory_mb < 50, f"Model memory usage too high: {memory_mb:.2f} MB"

    def test_cpu_compatibility(self):
        """Test that model works on CPU."""
        model = create_ar_model()
        model.cpu()
        
        batch_size = 1
        seq_len = 5
        input_dim = 768
        
        rf_tokens = torch.randn(batch_size, seq_len, input_dim)
        
        # Test forward pass on CPU
        with torch.no_grad():
            logits, loss = model(rf_tokens)
        
        assert logits.device.type == 'cpu'
        assert loss is None or loss.device.type == 'cpu'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])