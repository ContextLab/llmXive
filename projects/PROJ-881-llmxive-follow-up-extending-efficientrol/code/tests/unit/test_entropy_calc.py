import pytest
import numpy as np
import sys
import os
import torch
from src.utils.entropy_calc import (
    calculate_entropy,
    compute_shannon_entropy,
    compute_batch_entropy,
    compute_layer_wise_entropy
)


class TestCalculateEntropy:
    """Unit tests for calculate_entropy function."""

    def test_valid_1d_input(self):
        """Test with a valid 1D probability distribution."""
        probs = torch.tensor([0.1, 0.2, 0.3, 0.4])
        entropy = calculate_entropy(probs)
        assert isinstance(entropy, float)
        assert entropy > 0
        assert entropy < 2.0  # Max entropy for 4 items is log(4) ≈ 1.386

    def test_valid_2d_input(self):
        """Test with a valid 2D batch of probability distributions."""
        probs = torch.tensor([
            [0.1, 0.2, 0.3, 0.4],
            [0.25, 0.25, 0.25, 0.25]
        ])
        entropy = calculate_entropy(probs)
        assert isinstance(entropy, float)
        assert entropy > 0

    def test_clamp_prevents_log_zero(self):
        """
        Semantic Test: The function MUST correctly handle near-zero probability inputs
        by returning a finite value without crashing.
        Specifically, test that input probabilities resulting in p=0.0 (after clamping)
        do not cause log(0) errors.
        """
        # Create a distribution with exact zeros
        probs = torch.tensor([0.0, 0.0, 1.0])
        
        # This should NOT raise an error due to log(0)
        entropy = calculate_entropy(probs)
        
        # The result must be finite
        assert np.isfinite(entropy)
        
        # The result should be 0.0 because p*log(p) for p=0 is 0, and for p=1 is 0
        # H = - (0*log(0) + 0*log(0) + 1*log(1)) = 0
        # Note: With clamping, 0 becomes 1e-9, so we get a very small positive number
        # but it should still be finite and close to 0
        assert entropy >= 0.0
        assert entropy < 1e-5  # Should be very close to 0

    def test_clamp_with_extreme_values(self):
        """Test with extremely small probabilities."""
        probs = torch.tensor([1e-20, 1e-20, 1.0 - 2e-20])
        entropy = calculate_entropy(probs)
        assert np.isfinite(entropy)
        assert entropy >= 0.0

    def test_uniform_distribution(self):
        """Test with uniform distribution (maximum entropy)."""
        n = 10
        probs = torch.ones(n) / n
        entropy = calculate_entropy(probs)
        expected = np.log(n)
        assert np.isclose(entropy, expected, rtol=1e-5)

    def test_gpu_tensor_rejected(self):
        """Test that GPU tensors are rejected."""
        if torch.cuda.is_available():
            probs = torch.tensor([0.5, 0.5]).cuda()
            with pytest.raises(ValueError, match="must be on CPU"):
                calculate_entropy(probs)
        else:
            # Skip if no CUDA
            pytest.skip("CUDA not available")

    def test_empty_tensor_rejected(self):
        """Test that empty tensors are rejected."""
        probs = torch.tensor([])
        with pytest.raises(ValueError, match="empty"):
            calculate_entropy(probs)

    def test_wrong_dimensions_rejected(self):
        """Test that tensors with wrong dimensions are rejected."""
        probs = torch.tensor([[[0.5, 0.5]]])  # 3D tensor
        with pytest.raises(ValueError, match="must be 1D or 2D"):
            calculate_entropy(probs)

    def test_numpy_input(self):
        """Test that numpy arrays are accepted."""
        probs = np.array([0.5, 0.5])
        entropy = calculate_entropy(probs)
        assert isinstance(entropy, float)
        assert np.isclose(entropy, np.log(2), rtol=1e-5)


class TestComputeShannonEntropy:
    """Unit tests for compute_shannon_entropy alias."""

    def test_alias_functionality(self):
        """Test that compute_shannon_entropy is an alias for calculate_entropy."""
        probs = torch.tensor([0.2, 0.3, 0.5])
        entropy1 = calculate_entropy(probs)
        entropy2 = compute_shannon_entropy(probs)
        assert entropy1 == entropy2


class TestComputeBatchEntropy:
    """Unit tests for compute_batch_entropy function."""

    def test_batch_processing(self):
        """Test batch entropy calculation."""
        batch_probs = torch.tensor([
            [0.5, 0.5],
            [0.1, 0.9],
            [0.33, 0.67]
        ])
        entropies = compute_batch_entropy(batch_probs)
        
        assert len(entropies) == 3
        assert all(isinstance(e, float) for e in entropies)
        assert all(np.isfinite(e) for e in entropies)
        
        # First should be max entropy (log(2))
        assert np.isclose(entropies[0], np.log(2), rtol=1e-5)

    def test_batch_with_zeros(self):
        """Test batch with zero probabilities."""
        batch_probs = torch.tensor([
            [0.0, 1.0],
            [1.0, 0.0]
        ])
        entropies = compute_batch_entropy(batch_probs)
        
        assert len(entropies) == 2
        assert all(np.isfinite(e) for e in entropies)
        # Both should be close to 0
        assert all(e < 1e-5 for e in entropies)


class TestComputeLayerWiseEntropy:
    """Unit tests for compute_layer_wise_entropy function."""

    def test_layer_wise_calculation(self):
        """Test layer-wise entropy calculation."""
        # Shape: [batch=2, layers=3, vocab=4]
        logits = torch.randn(2, 3, 4)
        results = compute_layer_wise_entropy(logits)
        
        assert len(results) == 3
        assert all(isinstance(v, list) for v in results.values())
        assert all(len(v) == 2 for v in results.values())  # 2 batch items
        assert all(all(np.isfinite(e) for e in layer_entropies) 
                  for layer_entropies in results.values())

    def test_selected_layers(self):
        """Test with specific layer indices."""
        logits = torch.randn(2, 5, 4)  # 5 layers
        results = compute_layer_wise_entropy(logits, layer_indices=[0, 2, 4])
        
        assert len(results) == 3
        assert all(idx in results for idx in [0, 2, 4])

    def test_invalid_layer_index(self):
        """Test with out-of-range layer index."""
        logits = torch.randn(2, 3, 4)
        with pytest.raises(ValueError, match="out of range"):
            compute_layer_wise_entropy(logits, layer_indices=[5])

    def test_gpu_logits_rejected(self):
        """Test that GPU logits are rejected."""
        if torch.cuda.is_available():
            logits = torch.randn(2, 3, 4).cuda()
            with pytest.raises(ValueError, match="must be on CPU"):
                compute_layer_wise_entropy(logits)
        else:
            pytest.skip("CUDA not available")