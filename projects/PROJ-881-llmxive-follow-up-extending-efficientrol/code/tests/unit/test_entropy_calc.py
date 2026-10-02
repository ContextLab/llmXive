import pytest
import numpy as np
import sys
import os
import torch
from src.utils.entropy_calc import (
    calculate_entropy,
    compute_shannon_entropy,
    compute_batch_entropy,
    compute_layer_wise_entropy,
)


class TestCalculateEntropy:
    """Test the main calculate_entropy function."""

    def test_1d_uniform_distribution(self):
        """Test entropy calculation with uniform 1D distribution."""
        # Uniform distribution over 4 classes: p=0.25 for each
        # Entropy = -4 * (0.25 * log(0.25)) = log(4) ≈ 1.386
        probs = torch.tensor([0.25, 0.25, 0.25, 0.25])
        entropy = calculate_entropy(probs)
        expected = np.log(4)
        assert abs(entropy - expected) < 1e-6

    def test_2d_batch_uniform(self):
        """Test entropy calculation with 2D batch of uniform distributions."""
        # Two identical uniform distributions
        probs = torch.tensor([
            [0.25, 0.25, 0.25, 0.25],
            [0.25, 0.25, 0.25, 0.25]
        ])
        entropy = calculate_entropy(probs)
        expected = np.log(4)
        assert abs(entropy - expected) < 1e-6

    def test_deterministic_distribution(self):
        """Test entropy with a deterministic (one-hot) distribution."""
        # One class has probability 1.0, others 0.0
        # Entropy should be 0
        probs = torch.tensor([1.0, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        assert entropy < 1e-9

    def test_clamp_prevents_log_zero(self):
        """Test that near-zero probabilities are clamped to prevent log(0)."""
        # Create a distribution with one exact zero and one near-1
        # This should NOT crash and should return a finite value
        probs = torch.tensor([1.0, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        assert np.isfinite(entropy)
        assert entropy >= 0

    def test_near_zero_probabilities(self):
        """Test handling of very small but non-zero probabilities."""
        # Very small probabilities that would cause issues without clamping
        probs = torch.tensor([0.999999999, 1e-15, 1e-15, 1e-15])
        entropy = calculate_entropy(probs)
        assert np.isfinite(entropy)
        assert entropy >= 0

    def test_invalid_input_type(self):
        """Test that non-tensor/array input raises ValueError."""
        with pytest.raises(ValueError):
            calculate_entropy([0.1, 0.2, 0.3, 0.4])

    def test_gpu_tensor_raises_error(self):
        """Test that GPU tensor raises ValueError (we require CPU)."""
        if torch.cuda.is_available():
            probs = torch.tensor([0.5, 0.5]).cuda()
            with pytest.raises(ValueError):
                calculate_entropy(probs)
        else:
            # Skip if no CUDA
            pass

    def test_empty_tensor_raises_error(self):
        """Test that empty tensor raises ValueError."""
        probs = torch.tensor([])
        with pytest.raises(ValueError):
            calculate_entropy(probs)

    def test_3d_tensor_raises_error(self):
        """Test that 3D tensor raises ValueError."""
        probs = torch.randn(2, 3, 4)
        with pytest.raises(ValueError):
            calculate_entropy(probs)

    def test_numpy_input(self):
        """Test that numpy array input works correctly."""
        probs = np.array([0.5, 0.5])
        entropy = calculate_entropy(probs)
        expected = np.log(2)
        assert abs(entropy - expected) < 1e-6


class TestComputeShannonEntropy:
    """Test the compute_shannon_entropy alias function."""

    def test_alias_functionality(self):
        """Test that compute_shannon_entropy is an alias for calculate_entropy."""
        probs = torch.tensor([0.5, 0.5])
        entropy1 = compute_shannon_entropy(probs)
        entropy2 = calculate_entropy(probs)
        assert entropy1 == entropy2


class TestComputeBatchEntropy:
    """Test the compute_batch_entropy function."""

    def test_batch_entropy_values(self):
        """Test that batch entropy returns correct values for each item."""
        probs = torch.tensor([
            [0.5, 0.5],  # entropy = log(2)
            [1.0, 0.0],  # entropy = 0
        ])
        entropies = compute_batch_entropy(probs)
        assert len(entropies) == 2
        assert abs(entropies[0] - np.log(2)) < 1e-6
        assert entropies[1] < 1e-9

    def test_batch_invalid_dimensions(self):
        """Test that non-2D input raises ValueError."""
        with pytest.raises(ValueError):
            compute_batch_entropy(torch.tensor([0.5, 0.5]))


class TestComputeLayerWiseEntropy:
    """Test the compute_layer_wise_entropy function."""

    def test_layer_wise_basic(self):
        """Test basic layer-wise entropy calculation."""
        # Create logits for 2 batches, 3 layers, 4 vocab items
        logits = torch.randn(2, 3, 4)
        results = compute_layer_wise_entropy(logits)
        assert 0 in results
        assert 1 in results
        assert 2 in results
        assert len(results[0]) == 2  # 2 batches

    def test_layer_wise_with_indices(self):
        """Test layer-wise entropy with specific layer indices."""
        logits = torch.randn(2, 5, 4)
        results = compute_layer_wise_entropy(logits, layer_indices=[0, 2])
        assert 0 in results
        assert 2 in results
        assert 1 not in results
        assert 3 not in results

    def test_layer_wise_invalid_indices(self):
        """Test that out-of-range layer indices raise ValueError."""
        logits = torch.randn(2, 3, 4)
        with pytest.raises(ValueError):
            compute_layer_wise_entropy(logits, layer_indices=[5])

    def test_layer_wise_3d_requirement(self):
        """Test that non-3D input raises ValueError."""
        with pytest.raises(ValueError):
            compute_layer_wise_entropy(torch.randn(2, 4))

    def test_layer_wise_gpu_tensor(self):
        """Test that GPU logits raise ValueError."""
        if torch.cuda.is_available():
            logits = torch.randn(2, 3, 4).cuda()
            with pytest.raises(ValueError):
                compute_layer_wise_entropy(logits)
        else:
            pass  # Skip if no CUDA