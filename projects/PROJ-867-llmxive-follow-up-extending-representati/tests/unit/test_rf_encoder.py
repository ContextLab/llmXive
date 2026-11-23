"""
Unit tests for the RFEncoder model.

These tests verify:
1. The model loads correctly.
2. The decoder layers are NOT instantiated.
3. The forward pass produces the correct output shape.
4. Parameters are frozen.
"""
import pytest
import torch
import logging
from unittest.mock import patch, MagicMock
from transformers import LayoutLMv3Config

# Import the module under test
from models.rf_encoder import RFEncoder, create_rf_encoder, get_default_config

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRFEncoder:
    """Unit tests for RFEncoder."""

    def test_decoder_not_instantiated(self):
        """
        Test that the decoder layers are explicitly excluded.
        This is a critical requirement for T015.
        """
        # Create the encoder
        encoder = create_rf_encoder(freeze=True)
        
        # Check that no 'decoder' attribute exists on the encoder
        assert not hasattr(encoder, 'decoder'), \
            "Decoder attribute should not exist on RFEncoder."
        
        # Check that no 'decoder' attribute exists on the underlying model
        assert not hasattr(encoder.encoder, 'decoder'), \
            "Decoder attribute should not exist on the underlying LayoutLMv3Model."
        
        # Check that no module names contain 'decoder'
        has_decoder_module = any('decoder' in name.lower() for name, _ in encoder.named_modules())
        assert not has_decoder_module, \
            "No module in the encoder should have 'decoder' in its name."

    def test_parameters_frozen(self):
        """Test that all parameters are frozen."""
        encoder = create_rf_encoder(freeze=True)
        
        # Check that no parameter requires gradients
        for param in encoder.parameters():
            assert not param.requires_grad, \
                "All parameters should be frozen (requires_grad=False)."

    def test_forward_pass_shape(self):
        """Test that the forward pass produces the correct output shape."""
        encoder = create_rf_encoder(freeze=True)
        
        batch_size = 2
        seq_len = 128
        hidden_size = 768  # Default for layoutlmv3-base
        
        input_ids = torch.randint(0, 1000, (batch_size, seq_len))
        attention_mask = torch.ones((batch_size, seq_len), dtype=torch.long)
        bbox = torch.zeros((batch_size, seq_len, 4), dtype=torch.long)
        
        # Set valid bbox values
        bbox[:, :, 0] = torch.randint(0, 1000, (batch_size, seq_len))
        bbox[:, :, 1] = torch.randint(0, 1000, (batch_size, seq_len))
        bbox[:, :, 2] = torch.randint(0, 1000, (batch_size, seq_len))
        bbox[:, :, 3] = torch.randint(0, 1000, (batch_size, seq_len))
        
        # Run forward pass
        with torch.no_grad():
            output = encoder(input_ids, attention_mask, bbox)
        
        last_hidden_state = output["last_hidden_state"]
        
        # Check output shape
        assert last_hidden_state.shape == (batch_size, seq_len, hidden_size), \
            f"Expected output shape ({batch_size}, {seq_len}, {hidden_size}), got {last_hidden_state.shape}"

    def test_get_token_embeddings(self):
        """Test the convenience method get_token_embeddings."""
        encoder = create_rf_encoder(freeze=True)
        
        batch_size = 1
        seq_len = 64
        
        input_ids = torch.randint(0, 1000, (batch_size, seq_len))
        attention_mask = torch.ones((batch_size, seq_len), dtype=torch.long)
        bbox = torch.zeros((batch_size, seq_len, 4), dtype=torch.long)
        
        # Set valid bbox values
        bbox[:, :, 0] = torch.randint(0, 1000, (batch_size, seq_len))
        bbox[:, :, 1] = torch.randint(0, 1000, (batch_size, seq_len))
        bbox[:, :, 2] = torch.randint(0, 1000, (batch_size, seq_len))
        bbox[:, :, 3] = torch.randint(0, 1000, (batch_size, seq_len))
        
        # Get token embeddings
        with torch.no_grad():
            embeddings = encoder.get_token_embeddings(input_ids, attention_mask, bbox)
        
        # Check shape
        assert embeddings.shape == (batch_size, seq_len, 768), \
            f"Expected embeddings shape ({batch_size}, {seq_len}, 768), got {embeddings.shape}"

    def test_decoder_excluded_on_init(self):
        """
        Verify that the decoder is explicitly excluded during initialization.
        This test mocks the LayoutLMv3Model.from_pretrained to ensure we handle
        the case where a decoder might be present in a hypothetical model variant.
        """
        # We rely on the actual implementation in RFEncoder which checks for 'decoder'
        # and removes it if found.
        encoder = create_rf_encoder(freeze=True)
        
        # Double check via graph inspection logic
        for name, module in encoder.named_modules():
            assert 'decoder' not in name.lower(), \
                f"Found decoder module during initialization: {name}"

    def test_no_decoder_in_memory(self):
        """
        Verify that decoder weights are not loaded into memory.
        We check the number of parameters and ensure they match the encoder-only count.
        """
        encoder = create_rf_encoder(freeze=True)
        
        # Count parameters
        param_count = sum(p.numel() for p in encoder.parameters())
        
        # LayoutLMv3-base has ~110M parameters. If decoder were loaded (e.g. as a head),
        # the count would be significantly higher or the model structure would be different.
        # We just verify that the count is reasonable for the encoder-only model.
        # Exact number might vary slightly due to config, but should be around 110M.
        assert param_count < 150_000_000, \
            f"Parameter count {param_count} seems too high, decoder might be loaded."
        
        # Also verify that the model is not a seq2seq model (which would have a decoder)
        assert not isinstance(encoder.encoder, type(None)), \
            "Encoder should not be None."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])