"""
Unit tests for entropy calculation utilities.
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.entropy_calc import (
    compute_shannon_entropy,
    compute_batch_entropy,
    compute_layer_wise_entropy,
    calculate_entropy
)

class TestComputeShannonEntropy:
    def test_uniform_distribution(self):
        """Test entropy of uniform distribution (maximum entropy)."""
        probs = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = compute_shannon_entropy(probs)
        # log(4) ≈ 1.386
        expected = -np.sum(probs * np.log(probs))
        assert np.isclose(entropy, expected)

    def test_deterministic_distribution(self):
        """Test entropy of deterministic distribution (zero entropy)."""
        probs = np.array([1.0, 0.0, 0.0, 0.0])
        entropy = compute_shannon_entropy(probs)
        # Should be close to 0 due to clamping
        assert entropy < 1e-5

    def test_empty_input(self):
        """Test that empty input returns 0.0."""
        entropy = compute_shannon_entropy(np.array([]))
        assert entropy == 0.0

    def test_negative_values_raises_error(self):
        """Test that negative probabilities raise ValueError."""
        with pytest.raises(ValueError):
            compute_shannon_entropy(np.array([-0.1, 1.1]))

    def test_list_input(self):
        """Test that list input works correctly."""
        probs = [0.5, 0.5]
        entropy = compute_shannon_entropy(probs)
        assert np.isclose(entropy, np.log(2))

class TestComputeBatchEntropy:
    def test_batch_of_two(self):
        """Test batch processing of two distributions."""
        batch = [[0.5, 0.5], [0.9, 0.1]]
        entropies = compute_batch_entropy(batch)
        assert len(entropies) == 2
        assert np.isclose(entropies[0], np.log(2))

    def test_2d_numpy_array(self):
        """Test with 2D numpy array input."""
        batch = np.array([[0.5, 0.5], [0.9, 0.1]])
        entropies = compute_batch_entropy(batch)
        assert len(entropies) == 2

    def test_invalid_dimensions(self):
        """Test that 1D array raises ValueError."""
        with pytest.raises(ValueError):
            compute_batch_entropy(np.array([0.5, 0.5]))

class TestComputeLayerWiseEntropy:
    def test_layer_wise_computation(self):
        """Test entropy calculation from raw logits."""
        logits = np.array([[2.0, 1.0, 0.0], [0.1, 0.2, 0.3]])
        entropies = compute_layer_wise_entropy(logits)
        assert len(entropies) == 2
        # Both should be positive values
        assert all(e > 0 for e in entropies)

    def test_softmax_conversion(self):
        """Verify that softmax is applied correctly."""
        logits = np.array([[100.0, 0.0, 0.0]])
        entropies = compute_layer_wise_entropy(logits)
        # Very low entropy due to high confidence
        assert entropies[0] < 0.1

class TestCalculateEntropy:
    def test_basic_entropy(self):
        """Test basic entropy calculation from logits."""
        logits = np.array([2.0, 1.0, 0.0])
        entropy = calculate_entropy(logits)
        assert entropy > 0
        assert isinstance(entropy, float)

    def test_clamp_prevents_log_zero(self):
        """
        T004 Core Test: Assert that the function returns a finite value
        for input logits resulting in p=0.0 (after softmax).
        
        We use extreme logits that would result in one probability being
        effectively 0.0 (e.g., [100.0, 0.0, 0.0] -> [~1.0, ~0.0, ~0.0]).
        Without clamping, log(0) would cause a runtime error or NaN.
        With clamping, we should get a finite entropy value.
        """
        # Create logits that result in extreme probabilities
        # [100.0, 0.0, 0.0] -> softmax -> [~1.0, ~0.0, ~0.0]
        extreme_logits = np.array([100.0, 0.0, 0.0])
        
        # This should NOT raise an error and should return a finite value
        entropy = calculate_entropy(extreme_logits)
        
        # Assert the result is finite (not NaN or Inf)
        assert np.isfinite(entropy), f"Entropy value {entropy} is not finite"
        
        # The entropy should be very low (high confidence) but positive
        assert entropy >= 0.0
        assert entropy < 0.1  # Should be very close to 0

    def test_type_error_on_non_array(self):
        """Test that non-numpy array input raises TypeError."""
        with pytest.raises(TypeError):
            calculate_entropy([1.0, 2.0, 3.0])

    def test_value_error_on_2d(self):
        """Test that 2D input raises ValueError."""
        with pytest.raises(ValueError):
            calculate_entropy(np.array([[1.0, 2.0], [3.0, 4.0]]))