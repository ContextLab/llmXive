import pytest
import torch
import torch.nn as nn
import numpy as np
import sys
from pathlib import Path

# Add code directory to path to allow imports from src
code_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_root / "code"))

from src.models.attention_net import ReactionAttentionNet

class TestAttentionNetArchitecture:
    """
    Unit tests for the model architecture construction in ReactionAttentionNet.
    Verifies that the model can be instantiated with various configurations
    and that forward passes produce tensors of the expected shape.
    """

    @pytest.fixture
    def config_defaults(self):
        """Default configuration for model tests."""
        return {
            "spectrum_dim": 1024,
            "fingerprint_dim": 2048,
            "condition_dim": 128,
            "hidden_dim": 256,
            "num_heads": 8,
            "num_layers": 2,
            "dropout": 0.1
        }

    def test_model_instantiation(self, config_defaults):
        """Test that the model can be instantiated without errors."""
        model = ReactionAttentionNet(
            spectrum_dim=config_defaults["spectrum_dim"],
            fingerprint_dim=config_defaults["fingerprint_dim"],
            condition_dim=config_defaults["condition_dim"],
            hidden_dim=config_defaults["hidden_dim"],
            num_heads=config_defaults["num_heads"],
            num_layers=config_defaults["num_layers"],
            dropout=config_defaults["dropout"]
        )
        assert model is not None
        assert isinstance(model, nn.Module)

    def test_forward_pass_shapes(self, config_defaults):
        """Test that forward pass produces output of correct shape."""
        model = ReactionAttentionNet(**config_defaults)
        batch_size = 32
        
        # Create dummy inputs
        # Spectra: [batch, seq_len, spectrum_dim]
        spectra = torch.randn(batch_size, 100, config_defaults["spectrum_dim"])
        # Fingerprints: [batch, fingerprint_dim]
        fingerprints = torch.randn(batch_size, config_defaults["fingerprint_dim"])
        # Conditions: [batch, condition_dim]
        conditions = torch.randn(batch_size, config_defaults["condition_dim"])
        
        model.eval()
        with torch.no_grad():
            output = model(spectra, fingerprints, conditions)
        
        # Output should be [batch, 1] for regression (DFT energy)
        assert output.shape == (batch_size, 1), f"Expected shape ({batch_size}, 1), got {output.shape}"

    def test_single_layer_model(self, config_defaults):
        """Test model with a single attention layer."""
        config = config_defaults.copy()
        config["num_layers"] = 1
        model = ReactionAttentionNet(**config)
        
        batch_size = 4
        spectra = torch.randn(batch_size, 50, config["spectrum_dim"])
        fingerprints = torch.randn(batch_size, config["fingerprint_dim"])
        conditions = torch.randn(batch_size, config["condition_dim"])
        
        model.eval()
        with torch.no_grad():
            output = model(spectra, fingerprints, conditions)
        
        assert output.shape == (batch_size, 1)

    def test_single_head_attention(self, config_defaults):
        """Test model with single attention head."""
        config = config_defaults.copy()
        config["num_heads"] = 1
        model = ReactionAttentionNet(**config)
        
        batch_size = 8
        spectra = torch.randn(batch_size, 64, config["spectrum_dim"])
        fingerprints = torch.randn(batch_size, config["fingerprint_dim"])
        conditions = torch.randn(batch_size, config["condition_dim"])
        
        model.eval()
        with torch.no_grad():
            output = model(spectra, fingerprints, conditions)
        
        assert output.shape == (batch_size, 1)

    def test_various_sequence_lengths(self, config_defaults):
        """Test model with different spectrum sequence lengths."""
        model = ReactionAttentionNet(**config_defaults)
        fingerprints = torch.randn(1, config_defaults["fingerprint_dim"])
        conditions = torch.randn(1, config_defaults["condition_dim"])
        
        model.eval()
        with torch.no_grad():
            for seq_len in [10, 50, 100, 200]:
                spectra = torch.randn(1, seq_len, config_defaults["spectrum_dim"])
                output = model(spectra, fingerprints, conditions)
                assert output.shape == (1, 1), f"Failed for seq_len={seq_len}"

    def test_dropout_layers_present(self, config_defaults):
        """Verify that dropout layers are present in the model."""
        model = ReactionAttentionNet(**config_defaults)
        
        # Check that the model has dropout layers
        has_dropout = any(isinstance(module, nn.Dropout) for module in model.modules())
        assert has_dropout, "Model should contain Dropout layers"

    def test_parameters_count(self, config_defaults):
        """Verify that the model has a reasonable number of parameters."""
        model = ReactionAttentionNet(**config_defaults)
        total_params = sum(p.numel() for p in model.parameters())
        
        # Should have a non-trivial number of parameters
        assert total_params > 0, "Model should have parameters"
        # Basic sanity check: shouldn't be tiny
        assert total_params > 1000, f"Model seems too small: {total_params} params"

    def test_requires_grad_default(self, config_defaults):
        """Verify that parameters require gradients by default."""
        model = ReactionAttentionNet(**config_defaults)
        
        for param in model.parameters():
            assert param.requires_grad, "All parameters should require gradients by default"

    def test_training_mode(self, config_defaults):
        """Test that model switches between train and eval modes correctly."""
        model = ReactionAttentionNet(**config_defaults)
        
        assert model.training, "Model should be in training mode by default"
        
        model.eval()
        assert not model.training, "Model should be in eval mode after eval()"
        
        model.train()
        assert model.training, "Model should be in training mode after train()"

    def test_input_dtype_preservation(self, config_defaults):
        """Test that output dtype matches input dtype."""
        model = ReactionAttentionNet(**config_defaults)
        
        batch_size = 4
        spectra = torch.randn(batch_size, 50, config_defaults["spectrum_dim"], dtype=torch.float64)
        fingerprints = torch.randn(batch_size, config_defaults["fingerprint_dim"], dtype=torch.float64)
        conditions = torch.randn(batch_size, config_defaults["condition_dim"], dtype=torch.float64)
        
        model.double()
        model.eval()
        
        with torch.no_grad():
            output = model(spectra, fingerprints, conditions)
        
        assert output.dtype == torch.float64, f"Output dtype {output.dtype} doesn't match input float64"

    def test_gradient_flow(self, config_defaults):
        """Test that gradients flow through the model."""
        model = ReactionAttentionNet(**config_defaults)
        model.train()
        
        batch_size = 4
        spectra = torch.randn(batch_size, 50, config_defaults["spectrum_dim"], requires_grad=True)
        fingerprints = torch.randn(batch_size, config_defaults["fingerprint_dim"])
        conditions = torch.randn(batch_size, config_defaults["condition_dim"])
        
        output = model(spectra, fingerprints, conditions)
        loss = output.sum()
        loss.backward()
        
        # Check that gradients were computed for at least some parameters
        has_grad = any(p.grad is not None for p in model.parameters())
        assert has_grad, "At least some parameters should have gradients after backward"

    def test_zero_input_handling(self, config_defaults):
        """Test model behavior with zero inputs (should not crash)."""
        model = ReactionAttentionNet(**config_defaults)
        model.eval()
        
        batch_size = 2
        spectra = torch.zeros(batch_size, 50, config_defaults["spectrum_dim"])
        fingerprints = torch.zeros(batch_size, config_defaults["fingerprint_dim"])
        conditions = torch.zeros(batch_size, config_defaults["condition_dim"])
        
        with torch.no_grad():
            output = model(spectra, fingerprints, conditions)
        
        # Output should be finite values (not NaN or Inf)
        assert torch.isfinite(output).all(), "Output should contain only finite values"

    def test_attention_head_dimensionality(self, config_defaults):
        """Test that attention head dimension is correctly derived."""
        hidden_dim = config_defaults["hidden_dim"]
        num_heads = config_defaults["num_heads"]
        
        # The model should be able to handle the division of hidden_dim by num_heads
        model = ReactionAttentionNet(**config_defaults)
        
        # Verify hidden_dim is divisible by num_heads (standard requirement for multi-head attention)
        assert hidden_dim % num_heads == 0, "hidden_dim must be divisible by num_heads"

    def test_output_layer_structure(self, config_defaults):
        """Test that the output layer maps to a single scalar for regression."""
        model = ReactionAttentionNet(**config_defaults)
        
        # The final layer should output 1 value per sample
        # Check the last linear layer in the model
        output_layer = None
        for module in model.modules():
            if isinstance(module, nn.Linear):
                output_layer = module
        
        assert output_layer is not None, "Model should have at least one Linear layer"
        # The final linear layer should output 1 feature (for regression target)
        # Note: This is a structural check; the exact final layer might vary by implementation
        assert output_layer.out_features == 1, f"Output layer should produce 1 feature, got {output_layer.out_features}"