"""
Unit tests for entropy calculation utilities.
"""

import pytest
import numpy as np
import sys
import os
import torch
from src.utils.entropy_calc import (
    compute_shannon_entropy,
    compute_batch_entropy,
    compute_layer_wise_entropy,
    calculate_entropy
)


class TestCalculateEntropy:
    """Tests for the calculate_entropy function (T004 primary API)."""

    def test_basic_entropy_calculation(self):
        """Test basic entropy calculation with uniform distribution."""
        # Uniform distribution over 2 elements: entropy = log(2) ≈ 0.693
        logits = np.array([0.0, 0.0])
        entropy = calculate_entropy(logits)
        assert abs(entropy - np.log(2)) < 1e-6

    def test_torch_tensor_input(self):
        """Test that torch tensors are handled correctly."""
        logits = torch.tensor([1.0, 2.0, 3.0])
        entropy = calculate_entropy(logits)
        assert isinstance(entropy, float)
        assert entropy > 0

    def test_high_confidence_low_entropy(self):
        """Test that high confidence (one dominant logit) yields low entropy."""
        logits = np.array([10.0, 0.0, 0.0])
        entropy = calculate_entropy(logits)
        assert entropy < 0.1  # Very low entropy

    def test_clamp_prevents_log_zero(self):
        """
        Test that the function returns a finite value for input logits 
        resulting in p=0.0 (or effectively 0).
        
        This specifically tests the clamping logic required by T004:
        probabilities < 1e-9 are clamped to 1e-9 BEFORE log, preventing
        log(0) errors.
        """
        # Create logits that result in extremely small probabilities
        # e.g., [100, 0, 0] -> softmax([100, 0, 0]) ≈ [1, ~0, ~0]
        # The ~0 values would be < 1e-9 and should be clamped
        logits = np.array([100.0, 0.0, 0.0])
        
        # This should NOT raise a log(0) error
        entropy = calculate_entropy(logits)
        
        # The result must be finite
        assert np.isfinite(entropy), f"Entropy should be finite, got {entropy}"
        
        # Additionally, test with explicit extreme values
        extreme_logits = np.array([1000.0, -1000.0, -1000.0])
        entropy_extreme = calculate_entropy(extreme_logits)
        assert np.isfinite(entropy_extreme), f"Entropy should be finite for extreme inputs, got {entropy_extreme}"

    def test_input_types(self):
        """Test various input types."""
        # Numpy array
        logits_np = np.array([1.0, 2.0])
        assert isinstance(calculate_entropy(logits_np), float)
        
        # Torch tensor
        logits_torch = torch.tensor([1.0, 2.0])
        assert isinstance(calculate_entropy(logits_torch), float)

    def test_dimensionality_check(self):
        """Test that non-1D inputs raise an error."""
        with pytest.raises(ValueError):
            calculate_entropy(np.array([[1.0, 2.0], [3.0, 4.0]]))
        
        with pytest.raises(ValueError):
            calculate_entropy(torch.tensor([[1.0, 2.0], [3.0, 4.0]]))


class TestComputeShannonEntropy:
    """Tests for the compute_shannon_entropy function."""

    def test_uniform_distribution(self):
        """Test entropy of uniform distribution."""
        probs = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = compute_shannon_entropy(probs)
        # H = -4 * (0.25 * log(0.25)) = -log(0.25) = log(4)
        expected = -np.log(0.25)
        assert abs(entropy - expected) < 1e-6

    def test_deterministic_distribution(self):
        """Test entropy of deterministic distribution (should be 0)."""
        probs = np.array([1.0, 0.0, 0.0])
        entropy = compute_shannon_entropy(probs)
        # Due to clamping, p=0 becomes 1e-9, so entropy is very small but not exactly 0
        assert entropy < 1e-5

    def test_empty_input(self):
        """Test that empty input returns 0.0."""
        assert compute_shannon_entropy(np.array([])) == 0.0
        assert compute_shannon_entropy([]) == 0.0

    def test_negative_values_error(self):
        """Test that negative probabilities raise an error."""
        with pytest.raises(ValueError):
            compute_shannon_entropy(np.array([0.5, -0.5]))

    def test_type_error(self):
        """Test that invalid types raise an error."""
        with pytest.raises(TypeError):
            compute_shannon_entropy("invalid")

    def test_clamping_behavior(self):
        """Test that values < 1e-9 are clamped before log."""
        # Create a distribution with a very small probability
        probs = np.array([0.9999999999, 1e-15])
        entropy = compute_shannon_entropy(probs)
        assert np.isfinite(entropy)


class TestComputeBatchEntropy:
    """Tests for the compute_batch_entropy function."""

    def test_batch_calculation(self):
        """Test entropy calculation for a batch of distributions."""
        batch = [
            [0.5, 0.5],
            [0.9, 0.1]
        ]
        entropies = compute_batch_entropy(batch)
        
        assert len(entropies) == 2
        assert isinstance(entropies, list)
        assert all(isinstance(e, float) for e in entropies)
        
        # First should be log(2)
        assert abs(entropies[0] - np.log(2)) < 1e-6

    def test_numpy_batch_input(self):
        """Test with numpy array input."""
        batch = np.array([[0.5, 0.5], [0.9, 0.1]])
        entropies = compute_batch_entropy(batch)
        assert len(entropies) == 2

    def test_wrong_dimensions(self):
        """Test that non-2D input raises an error."""
        with pytest.raises(ValueError):
            compute_batch_entropy(np.array([0.5, 0.5]))


class TestComputeLayerWiseEntropy:
    """Tests for the compute_layer_wise_entropy function."""

    def test_layer_wise_calculation(self):
        """Test entropy calculation from raw logits."""
        logits = np.array([
            [2.0, 1.0, 0.0],
            [0.0, 0.0, 0.0]
        ])
        entropies = compute_layer_wise_entropy(logits)
        
        assert len(entropies) == 2
        assert all(isinstance(e, float) for e in entropies)
        
        # Second row is uniform, so entropy should be log(3)
        assert abs(entropies[1] - np.log(3)) < 1e-6

    def test_torch_layer_wise(self):
        """Test with torch tensor input (converted internally)."""
        logits = torch.tensor([[2.0, 1.0, 0.0]])
        entropies = compute_layer_wise_entropy(logits)
        assert len(entropies) == 1

    def test_wrong_dimensions(self):
        """Test that non-2D input raises an error."""
        with pytest.raises(ValueError):
            compute_layer_wise_entropy(np.array([1.0, 2.0, 3.0]))