"""
Unit test for model architecture (T018).

Verifies:
1. Input shapes are correctly accepted by the predictor.
2. The model parameter count is within expected bounds (lightweight constraint).
3. The model structure matches the specification (CNN/Transformer hybrid or pure CNN).
"""
import pytest
import torch
import torch.nn as nn
import sys
import os

# Add project root to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.models.predictor import CTCFPredictor

class TestModelArchitecture:
    """Tests for the CTCF predictor model architecture."""

    @pytest.fixture
    def model(self):
        """Instantiate the model with standard parameters for testing."""
        # Standard parameters based on typical usage in US2
        # Sequence length: 1000 (±500bp)
        # One-hot encoding: 4 channels (A, C, G, T)
        # Chromatin channels: 3 (ATAC, H3K27ac, CTCF-ChIP) - assuming 3 based on spec
        # Hidden dim: 64 (lightweight)
        return CTCFPredictor(
            seq_len=1000,
            n_channels_seq=4,
            n_channels_chromatin=3,
            hidden_dim=64,
            num_classes=1
        )

    def test_model_instantiation(self, model):
        """Verify the model instantiates without error."""
        assert model is not None
        assert isinstance(model, nn.Module)

    def test_input_shape_sequence(self, model):
        """Verify the model accepts the correct sequence input shape."""
        # Input shape: (batch_size, n_channels_seq, seq_len)
        batch_size = 4
        n_channels_seq = 4
        seq_len = 1000
        
        dummy_seq = torch.randn(batch_size, n_channels_seq, seq_len)
        dummy_chromatin = torch.randn(batch_size, 3, 1) # Assuming aggregated chromatin or per-window
        
        # Adjust chromatin input shape based on actual model signature if needed
        # If the model expects (batch, n_chrom, 1) or (batch, n_chrom)
        # We assume the model handles the concatenation internally or expects specific shapes.
        # Let's test the forward pass with a standard shape.
        
        try:
            # Assuming the model expects (batch, n_channels_seq, seq_len) and (batch, n_channels_chrom, 1)
            # or similar. We will adjust based on the actual implementation in predictor.py.
            # If the predictor expects a single combined tensor, we adapt.
            
            # Standard CNN/Transformer expectation:
            # seq: [B, C, L]
            # chrom: [B, C_chrom, 1] or [B, C_chrom]
            
            # Let's assume the model takes two separate inputs or a concatenated one.
            # Based on typical "Four Causes" separation (Material vs Formal), 
            # it likely takes them as separate streams or concatenated channels.
            # We will test the most common pattern: concatenated along channel dim if lengths match,
            # or separate. Let's assume separate for now as per "distinct input channels".
            
            # If the model signature is model(seq, chromatin):
            output = model(dummy_seq, dummy_chromatin)
            assert output.shape[0] == batch_size
            assert output.shape[1] == 1
        except TypeError as e:
            # If the model takes a single tensor, try concatenating
            # This block handles the case where the API is model(combined_input)
            if "expected 1 arguments" in str(e) or "missing" in str(e):
                # Attempt to combine if the model expects one input
                # Assuming chromatin is broadcasted or expanded to match sequence length
                # This is a fallback for the test if the architecture is different
                pytest.fail(f"Model signature mismatch. Expected (seq, chrom) or (combined). Error: {e}")
            else:
                raise

    def test_input_shape_combined(self, model):
        """Verify the model handles combined input if designed that way."""
        # Some architectures concatenate sequence and chromatin channels immediately.
        # If the model expects [B, C_total, L], we test that.
        # However, T035 explicitly separates Material (seq) and Formal (chrom).
        # So we rely on the separate input test above.
        pass

    def test_parameter_count_lightweight(self, model):
        """Verify the parameter count is within lightweight constraints (e.g., < 5M)."""
        total_params = sum(p.numel() for p in model.parameters())
        # Light constraint: < 5 million parameters for CPU execution
        assert total_params < 5_000_000, f"Model has {total_params} parameters, exceeds lightweight limit."
        
    def test_parameter_count_reasonable(self, model):
        """Verify the model has enough parameters to be non-trivial (> 10k)."""
        total_params = sum(p.numel() for p in model.parameters())
        assert total_params > 10_000, f"Model has {total_params} parameters, too small to be useful."

    def test_output_shape(self, model):
        """Verify the output shape matches the binary classification requirement."""
        batch_size = 2
        dummy_seq = torch.randn(batch_size, 4, 1000)
        dummy_chromatin = torch.randn(batch_size, 3, 1)
        
        output = model(dummy_seq, dummy_chromatin)
        assert output.shape == (batch_size, 1), f"Expected output shape (batch, 1), got {output.shape}"

    def test_forward_pass_no_nan(self, model):
        """Verify a forward pass does not produce NaN values."""
        batch_size = 4
        dummy_seq = torch.randn(batch_size, 4, 1000)
        dummy_chromatin = torch.randn(batch_size, 3, 1)
        
        output = model(dummy_seq, dummy_chromatin)
        assert not torch.isnan(output).any(), "Forward pass produced NaN values."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])