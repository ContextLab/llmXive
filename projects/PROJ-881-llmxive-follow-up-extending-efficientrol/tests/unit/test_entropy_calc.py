import pytest
import numpy as np
import torch
from src.utils.entropy_calc import calculate_entropy

class TestCalculateEntropy:
    """Unit tests for the calculate_entropy function."""

    def test_clamp_prevents_log_zero(self):
        """
        Verify that the entropy calculation handles zero probabilities
        correctly by clamping them before taking the logarithm.
        
        Test Input: A tensor where one class has probability 0.0 and 
                    another has 1.0 (or near 1.0).
        Expected Output: A finite entropy value (no NaN or Inf).
        """
        # Create a tensor representing a probability distribution
        # where one class has 0.0 probability and the other has 1.0.
        # Shape: [2] (two classes)
        probs = torch.tensor([0.0, 1.0], dtype=torch.float32)
        
        # Calculate entropy. The function should clamp 0.0 to 1e-9
        # internally to prevent log(0) errors.
        entropy = calculate_entropy(probs)
        
        # Assert that the result is a finite number (not NaN or Inf)
        assert np.isfinite(entropy), f"Entropy calculation resulted in non-finite value: {entropy}"
        
        # For a distribution [0, 1], the entropy should be 0.0
        # (since -1 * log(1) = 0). Due to clamping, it might be a very small number.
        assert entropy >= 0.0, f"Entropy should be non-negative, got: {entropy}"
        assert entropy < 1e-6, f"Entropy for deterministic distribution should be near zero, got: {entropy}"

    def test_batch_clamp_prevents_log_zero(self):
        """
        Test the clamp logic with a batch of probability distributions.
        """
        # Batch shape: [2, 3] (2 samples, 3 classes)
        # Sample 1: [0.0, 1.0, 0.0]
        # Sample 2: [0.5, 0.5, 0.0]
        probs = torch.tensor([
            [0.0, 1.0, 0.0],
            [0.5, 0.5, 0.0]
        ], dtype=torch.float32)
        
        entropy = calculate_entropy(probs)
        
        # The function returns a scalar mean entropy for the batch
        assert np.isfinite(entropy), f"Batch entropy calculation resulted in non-finite value: {entropy}"

    def test_normal_distribution(self):
        """
        Test with a standard uniform distribution to ensure correctness.
        """
        # Uniform distribution over 4 classes: [0.25, 0.25, 0.25, 0.25]
        # Entropy should be log(4) ≈ 1.386
        probs = torch.tensor([0.25, 0.25, 0.25, 0.25], dtype=torch.float32)
        
        entropy = calculate_entropy(probs)
        
        expected_entropy = np.log(4.0)
        assert np.isfinite(entropy), "Entropy should be finite"
        assert np.isclose(entropy, expected_entropy, atol=1e-5), \
            f"Expected entropy {expected_entropy}, got {entropy}"

    def test_very_small_probabilities(self):
        """
        Test with probabilities close to the clamp threshold.
        """
        # Create a distribution with very small probabilities
        probs = torch.tensor([1e-10, 1e-10, 1.0 - 2e-10], dtype=torch.float32)
        
        entropy = calculate_entropy(probs)
        
        assert np.isfinite(entropy), "Entropy should be finite even with very small probabilities"
        assert entropy >= 0.0, "Entropy should be non-negative"