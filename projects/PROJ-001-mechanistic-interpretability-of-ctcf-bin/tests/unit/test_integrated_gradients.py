"""
Unit test for integrated gradients attribution map shape.

This test verifies that the integrated gradients computation produces
attribution maps with the correct shape matching the input sequence
and chromatin feature dimensions.

Dependency: code/models/predictor.py (CTCFPredictor)
"""
import pytest
import torch
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from models.predictor import CTCFPredictor

# Constants for test
SEQUENCE_LENGTH = 1000  # ±500bp window
VOCAB_SIZE = 4  # A, C, G, T one-hot
NUM_CHROMATIN_FEATURES = 3  # ATAC-seq, H3K27ac, etc.
BATCH_SIZE = 2

def create_dummy_input():
    """Create a dummy input tensor matching the model's expected shape.
    
    Returns:
        torch.Tensor: Input tensor of shape (batch_size, seq_len, vocab_size + num_chromatin)
    """
    # Sequence one-hot: (batch, seq_len, 4)
    sequence = torch.randn(BATCH_SIZE, SEQUENCE_LENGTH, VOCAB_SIZE)
    # Chromatin features: (batch, seq_len, num_features)
    chromatin = torch.randn(BATCH_SIZE, SEQUENCE_LENGTH, NUM_CHROMATIN_FEATURES)
    
    # Concatenate along feature dimension
    # Shape: (batch, seq_len, 4 + 3) = (batch, seq_len, 7)
    input_tensor = torch.cat([sequence, chromatin], dim=-1)
    return input_tensor

def compute_integrated_gradients(model, input_tensor, n_steps=50):
    """
    Compute integrated gradients for the model's prediction.
    
    Integrated gradients: IG_i(x) = (x_i - x'_i) * ∫_{α=0}^{1} ∂F(x' + α(x-x'))/∂x_i dα
    
    Args:
        model: The CTCFPredictor model
        input_tensor: Input tensor of shape (batch, seq_len, features)
        n_steps: Number of integration steps
        
    Returns:
        torch.Tensor: Attribution map of shape (batch, seq_len, features)
    """
    model.eval()
    input_tensor = input_tensor.requires_grad_(True)
    
    # Baseline: zero tensor (or could be mean of dataset)
    baseline = torch.zeros_like(input_tensor)
    
    # Generate interpolated inputs
    alpha_values = torch.linspace(0, 1, n_steps).to(input_tensor.device)
    integrated_gradients = torch.zeros_like(input_tensor)
    
    for alpha in alpha_values:
        interpolated = baseline + alpha * (input_tensor - baseline)
        interpolated.requires_grad_(True)
        
        # Forward pass
        outputs = model(interpolated)
        # Use first sample's prediction (probability of binding)
        loss = outputs[0, 0]
        
        # Backward pass
        loss.backward()
        
        # Accumulate gradients
        integrated_gradients += interpolated.grad.detach()
    
    # Average over steps and multiply by (x - baseline)
    integrated_gradients = integrated_gradients / n_steps * (input_tensor - baseline)
    
    return integrated_gradients.detach()

class TestIntegratedGradientsShape:
    """Test suite for integrated gradients attribution map shape."""
    
    def test_attribution_map_shape_matches_input(self):
        """Verify attribution map has the same shape as input tensor."""
        model = CTCFPredictor(
            seq_len=SEQUENCE_LENGTH,
            vocab_size=VOCAB_SIZE,
            num_chromatin_features=NUM_CHROMATIN_FEATURES
        )
        
        input_tensor = create_dummy_input()
        attribution_map = compute_integrated_gradients(model, input_tensor)
        
        assert attribution_map.shape == input_tensor.shape, \
            f"Attribution map shape {attribution_map.shape} does not match input shape {input_tensor.shape}"
        
        # Explicit shape check
        assert attribution_map.shape[0] == BATCH_SIZE, "Batch dimension mismatch"
        assert attribution_map.shape[1] == SEQUENCE_LENGTH, "Sequence length dimension mismatch"
        assert attribution_map.shape[2] == VOCAB_SIZE + NUM_CHROMATIN_FEATURES, \
            f"Feature dimension mismatch: expected {VOCAB_SIZE + NUM_CHROMATIN_FEATURES}, got {attribution_map.shape[2]}"
    
    def test_attribution_map_is_non_zero(self):
        """Verify attribution map contains non-zero values for non-trivial inputs."""
        model = CTCFPredictor(
            seq_len=SEQUENCE_LENGTH,
            vocab_size=VOCAT_SIZE,
            num_chromatin_features=NUM_CHROMATIN_FEATURES
        )
        
        input_tensor = create_dummy_input()
        attribution_map = compute_integrated_gradients(model, input_tensor)
        
        # Check that at least some attributions are non-zero
        non_zero_count = torch.nonzero(attribution_map).size(0)
        assert non_zero_count > 0, "Attribution map is entirely zero"
    
    def test_attribution_map_dtype(self):
        """Verify attribution map has correct data type."""
        model = CTCFPredictor(
            seq_len=SEQUENCE_LENGTH,
            vocab_size=VOCAB_SIZE,
            num_chromatin_features=NUM_CHROMATIN_FEATURES
        )
        
        input_tensor = create_dummy_input()
        attribution_map = compute_integrated_gradients(model, input_tensor)
        
        assert attribution_map.dtype == input_tensor.dtype, \
            f"Attribution map dtype {attribution_map.dtype} does not match input dtype {input_tensor.dtype}"
    
    def test_sequence_vs_chromatin_attribution_split(self):
        """Verify that sequence and chromatin attributions can be separated."""
        model = CTCFPredictor(
            seq_len=SEQUENCE_LENGTH,
            vocab_size=VOCAB_SIZE,
            num_chromatin_features=NUM_CHROMATIN_FEATURES
        )
        
        input_tensor = create_dummy_input()
        attribution_map = compute_integrated_gradients(model, input_tensor)
        
        # Split attribution map into sequence and chromatin parts
        sequence_attribution = attribution_map[:, :, :VOCAB_SIZE]
        chromatin_attribution = attribution_map[:, :, VOCAB_SIZE:]
        
        assert sequence_attribution.shape == (BATCH_SIZE, SEQUENCE_LENGTH, VOCAB_SIZE)
        assert chromatin_attribution.shape == (BATCH_SIZE, SEQUENCE_LENGTH, NUM_CHROMATIN_FEATURES)
    
    def test_single_step_integration(self):
        """Test that integrated gradients work with a single integration step."""
        model = CTCFPredictor(
            seq_len=SEQUENCE_LENGTH,
            vocab_size=VOCAB_SIZE,
            num_chromatin_features=NUM_CHROMATIN_FEATURES
        )
        
        input_tensor = create_dummy_input()
        attribution_map = compute_integrated_gradients(model, input_tensor, n_steps=1)
        
        assert attribution_map.shape == input_tensor.shape
        
        # With n_steps=1, the attribution should be the gradient at α=0.5
        # multiplied by (x - baseline), which should be non-zero for random inputs
        assert torch.any(attribution_map != 0), "Single-step attribution is zero"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])