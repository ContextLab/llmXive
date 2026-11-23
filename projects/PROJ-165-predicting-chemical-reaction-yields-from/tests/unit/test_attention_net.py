import pytest
import torch
import torch.nn as nn
import numpy as np
import sys
from pathlib import Path

# Add project root to path to allow imports from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.models.attention_net import AttentionReactionNet


class TestAttentionNetArchitecture:
    """Unit tests for the AttentionReactionNet model architecture construction."""

    @pytest.fixture
    def default_config(self):
        """Provide a standard configuration for model construction."""
        return {
            "spectral_dim": 1024,      # Fixed grid size for resampled spectra
            "fingerprint_dim": 2048,   # ECFP4 vector size
            "condition_dim": 128,      # Encoded condition vector size
            "hidden_dim": 256,
            "num_heads": 4,
            "num_layers": 2,
            "dropout": 0.1,
            "target_dim": 1            # Normalized DFT energy
        }

    def test_model_instantiation(self, default_config):
        """Test that the model can be instantiated without errors."""
        model = AttentionReactionNet(**default_config)
        assert model is not None
        assert isinstance(model, nn.Module)

    def test_forward_pass_shapes(self, default_config):
        """Test that forward pass produces tensors of expected shapes."""
        model = AttentionReactionNet(**default_config)
        batch_size = 8

        # Create dummy inputs matching expected dimensions
        # spectral_input: [batch, spectral_dim]
        spectral_input = torch.randn(batch_size, default_config["spectral_dim"])
        # fingerprint_input: [batch, fingerprint_dim]
        fingerprint_input = torch.randn(batch_size, default_config["fingerprint_dim"])
        # condition_input: [batch, condition_dim]
        condition_input = torch.randn(batch_size, default_config["condition_dim"])

        model.eval()
        with torch.no_grad():
            output = model(spectral_input, fingerprint_input, condition_input)

        # Output should be [batch, target_dim] -> [batch, 1]
        assert output.shape == (batch_size, default_config["target_dim"])

    def test_forward_pass_with_masks(self, default_config):
        """Test forward pass with optional spectral masks."""
        model = AttentionReactionNet(**default_config)
        batch_size = 8

        spectral_input = torch.randn(batch_size, default_config["spectral_dim"])
        fingerprint_input = torch.randn(batch_size, default_config["fingerprint_dim"])
        condition_input = torch.randn(batch_size, default_config["condition_dim"])

        # Create a mask: 1 for valid, 0 for masked
        mask = torch.ones(batch_size, default_config["spectral_dim"])
        mask[:, -10:] = 0  # Mask the last 10 wavenumbers

        model.eval()
        with torch.no_grad():
            output = model(spectral_input, fingerprint_input, condition_input, mask=mask)

        assert output.shape == (batch_size, default_config["target_dim"])

    def test_parameter_count(self, default_config):
        """Test that the model has a non-zero number of parameters."""
        model = AttentionReactionNet(**default_config)
        total_params = sum(p.numel() for p in model.parameters())
        assert total_params > 0

    def test_gradient_flow(self, default_config):
        """Test that gradients flow through the model during backprop."""
        model = AttentionReactionNet(**default_config)
        batch_size = 4

        spectral_input = torch.randn(batch_size, default_config["spectral_dim"], requires_grad=True)
        fingerprint_input = torch.randn(batch_size, default_config["fingerprint_dim"], requires_grad=True)
        condition_input = torch.randn(batch_size, default_config["condition_dim"], requires_grad=True)
        target = torch.randn(batch_size, 1)

        model.train()
        output = model(spectral_input, fingerprint_input, condition_input)
        loss = nn.MSELoss()(output, target)
        loss.backward()

        # Check that gradients exist for input tensors (if they require them)
        assert spectral_input.grad is not None
        assert fingerprint_input.grad is not None
        assert condition_input.grad is not None

    def test_device_compatibility(self, default_config):
        """Test that the model can be moved to different devices (if available)."""
        model = AttentionReactionNet(**default_config)

        # Test CPU (always available)
        model_cpu = model.cpu()
        assert next(model_cpu.parameters()).device.type == "cpu"

        # Test CUDA if available
        if torch.cuda.is_available():
            model_cuda = model.cuda()
            assert next(model_cuda.parameters()).device.type == "cuda"
        else:
            # Skip CUDA test if not available
            pytest.skip("CUDA not available")

    def test_attention_head_dimension(self, default_config):
        """Test that attention heads are correctly sized."""
        model = AttentionReactionNet(**default_config)
        # The hidden_dim should be divisible by num_heads for multi-head attention
        assert default_config["hidden_dim"] % default_config["num_heads"] == 0

    def test_dropout_configuration(self, default_config):
        """Test that dropout layers are present and configured correctly."""
        model = AttentionReactionNet(**default_config)
        dropout_layers = [m for m in model.modules() if isinstance(m, nn.Dropout)]
        assert len(dropout_layers) > 0
        for layer in dropout_layers:
            assert layer.p == default_config["dropout"]

    def test_invalid_dimensions_raise_error(self):
        """Test that invalid dimension configurations raise appropriate errors."""
        invalid_config = {
            "spectral_dim": 1024,
            "fingerprint_dim": 2048,
            "condition_dim": 128,
            "hidden_dim": 256,
            "num_heads": 7,  # 7 does not divide 256
            "num_layers": 2,
            "dropout": 0.1,
            "target_dim": 1
        }
        # This should raise an error during model construction or forward pass
        model = AttentionReactionNet(**invalid_config)
        # Attempt a forward pass to trigger the dimension mismatch
        spectral_input = torch.randn(2, 1024)
        fingerprint_input = torch.randn(2, 2048)
        condition_input = torch.randn(2, 128)

        with pytest.raises((RuntimeError, AssertionError)):
            model(spectral_input, fingerprint_input, condition_input)