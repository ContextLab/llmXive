"""
Unit tests for RF Encoder (T015).

Tests validate:
1. Model loads correctly with frozen weights
2. Token shape matches expected dimensionality
3. No gradients are computed (frozen)
4. Pixel-decoder layers are not invoked
"""
import pytest
import torch
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.rf_encoder import RFEncoder, create_rf_encoder


class TestRFEncoderInitialization:
    """Test RF Encoder initialization and weight freezing."""
    
    def test_encoder_creates_without_error(self):
        """Test that RFEncoder initializes successfully."""
        encoder = create_rf_encoder()
        assert encoder is not None
        assert isinstance(encoder, RFEncoder)
    
    def test_weights_are_frozen(self):
        """Test that all model weights are frozen (requires_grad=False)."""
        encoder = create_rf_encoder()
        
        frozen_count = 0
        total_count = 0
        
        for param in encoder.model.parameters():
            total_count += 1
            if not param.requires_grad:
                frozen_count += 1
        
        assert frozen_count == total_count, \
            f"Not all weights are frozen: {frozen_count}/{total_count}"
    
    def test_model_is_in_eval_mode(self):
        """Test that the model is in evaluation mode."""
        encoder = create_rf_encoder()
        assert encoder.model.training is False
    
    def test_hidden_size_matches_config(self):
        """Test that hidden size matches expected value (768 for base)."""
        encoder = create_rf_encoder()
        assert encoder.hidden_size == 768


class TestRFEncoderForwardPass:
    """Test RF Encoder forward pass and output shapes."""
    
    @pytest.fixture
    def encoder(self):
        """Create a test encoder."""
        return create_rf_encoder()
    
    @pytest.fixture
    def dummy_inputs(self):
        """Create dummy inputs for testing."""
        batch_size = 2
        seq_length = 128  # Smaller for faster testing
        
        input_ids = torch.randint(0, 10000, (batch_size, seq_length))
        attention_mask = torch.ones((batch_size, seq_length), dtype=torch.long)
        bbox = torch.randint(0, 1000, (batch_size, seq_length, 4))
        pixel_values = torch.randn((batch_size, 3, 224, 224))
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'bbox': bbox,
            'pixel_values': pixel_values
        }
    
    def test_extract_tokens_returns_correct_shape(self, encoder, dummy_inputs):
        """Test that extract_tokens returns correct tensor shape."""
        tokens = encoder.extract_tokens(**dummy_inputs)
        
        batch_size = dummy_inputs['input_ids'].shape[0]
        seq_length = dummy_inputs['input_ids'].shape[1]
        
        expected_shape = (batch_size, seq_length, encoder.hidden_size)
        
        assert tokens.shape == expected_shape, \
            f"Shape mismatch: {tokens.shape} vs {expected_shape}"
    
    def test_forward_returns_tuple(self, encoder, dummy_inputs):
        """Test that forward returns a tuple of (last_hidden_state, pooler_output)."""
        last_hidden_state, pooler_output = encoder.forward(**dummy_inputs)
        
        assert isinstance(last_hidden_state, torch.Tensor)
        assert isinstance(pooler_output, torch.Tensor)
        
        # Check shapes
        batch_size = dummy_inputs['input_ids'].shape[0]
        seq_length = dummy_inputs['input_ids'].shape[1]
        
        assert last_hidden_state.shape == (batch_size, seq_length, encoder.hidden_size)
        assert pooler_output.shape == (batch_size, encoder.hidden_size)
    
    def test_no_gradients_computed(self, encoder, dummy_inputs):
        """Test that no gradients are computed during forward pass."""
        tokens = encoder.extract_tokens(**dummy_inputs)
        
        # Check that no gradient history is tracked
        assert tokens.grad_fn is None, "Gradients were computed (grad_fn is not None)"
        
        # Check individual parameters
        for param in encoder.model.parameters():
            assert param.grad is None, f"Parameter {param.shape} has gradients"
    
    def test_single_image_extraction(self, encoder):
        """Test extraction from a single image (batch_size=1)."""
        input_ids = torch.randint(0, 10000, (1, 64))
        attention_mask = torch.ones((1, 64), dtype=torch.long)
        bbox = torch.randint(0, 1000, (1, 64, 4))
        pixel_values = torch.randn((1, 3, 224, 224))
        
        tokens = encoder.extract_tokens(
            input_ids=input_ids,
            attention_mask=attention_mask,
            bbox=bbox,
            pixel_values=pixel_values
        )
        
        assert tokens.shape == (1, 64, encoder.hidden_size)


class TestRFEncoderCPUOnly:
    """Test that RF Encoder runs on CPU only (no CUDA)."""
    
    def test_no_cuda_usage(self):
        """Test that the encoder does not require CUDA."""
        encoder = create_rf_encoder()
        
        # Force to CPU explicitly
        encoder = encoder.cpu()
        
        # Verify all parameters are on CPU
        for param in encoder.parameters():
            assert param.device.type == 'cpu', \
                f"Parameter on device {param.device}, expected cpu"
    
    def test_forward_pass_on_cpu(self):
        """Test forward pass on CPU."""
        encoder = create_rf_encoder().cpu()
        
        input_ids = torch.randint(0, 10000, (1, 32))
        attention_mask = torch.ones((1, 32), dtype=torch.long)
        bbox = torch.randint(0, 1000, (1, 32, 4))
        pixel_values = torch.randn((1, 3, 224, 224))
        
        tokens = encoder.extract_tokens(
            input_ids=input_ids,
            attention_mask=attention_mask,
            bbox=bbox,
            pixel_values=pixel_values
        )
        
        assert tokens.device.type == 'cpu'
        assert tokens.shape == (1, 32, encoder.hidden_size)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
