"""
Unit tests for magnitude-only control experiment.

Tests that the magnitude-only probability calculation correctly
implements P = ||c1||^2 + ||c2||^2 without phase interactions.
"""
import torch
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from experiments.run_magnitude_control import compute_magnitude_only_probability


def test_magnitude_only_constructive():
    """
    Test that magnitude-only control produces expected results for
    constructive cases (both vectors pointing in same direction).
    """
    # Create two identical vectors
    c1 = torch.complex(torch.tensor([1.0, 0.0]), torch.zeros(2))
    c2 = torch.complex(torch.tensor([1.0, 0.0]), torch.zeros(2))
    
    prob = compute_magnitude_only_probability(c1.unsqueeze(0), c2.unsqueeze(0))
    
    # Both have magnitude 1, so sum of squares = 2
    # After normalization, each should contribute equally
    expected = torch.tensor([0.5])  # Normalized
    
    assert torch.allclose(prob, expected, atol=1e-5), \
        f"Expected {expected}, got {prob}"


def test_magnitude_only_destructive_magnitudes():
    """
    Test that magnitude-only control ignores phase and only considers magnitudes.
    Even with opposite phases, magnitudes add up.
    """
    # Create vectors with opposite phases but same magnitude
    c1 = torch.complex(torch.tensor([1.0, 0.0]), torch.zeros(2))
    c2 = torch.complex(torch.tensor([-1.0, 0.0]), torch.zeros(2))
    
    prob = compute_magnitude_only_probability(c1.unsqueeze(0), c2.unsqueeze(0))
    
    # Magnitudes are both 1, so sum of squares = 2
    # After normalization, should be 0.5 each (same as constructive case)
    expected = torch.tensor([0.5])
    
    assert torch.allclose(prob, expected, atol=1e-5), \
        f"Magnitude-only should ignore phase, expected {expected}, got {prob}"


def test_magnitude_only_different_magnitudes():
    """
    Test magnitude-only with different magnitude vectors.
    """
    # c1 has magnitude 2, c2 has magnitude 1
    c1 = torch.complex(torch.tensor([2.0, 0.0]), torch.zeros(2))
    c2 = torch.complex(torch.tensor([1.0, 0.0]), torch.zeros(2))
    
    prob = compute_magnitude_only_probability(c1.unsqueeze(0), c2.unsqueeze(0))
    
    # ||c1||^2 = 4, ||c2||^2 = 1, sum = 5
    # P(c1) = 4/5 = 0.8, P(c2) = 1/5 = 0.2
    expected = torch.tensor([0.8])
    
    assert torch.allclose(prob, expected, atol=1e-5), \
        f"Expected {expected}, got {prob}"


def test_magnitude_only_batch():
    """
    Test magnitude-only with batched inputs.
    """
    batch_size = 3
    c1 = torch.complex(torch.ones(batch_size, 2), torch.zeros(batch_size, 2))
    c2 = torch.complex(torch.ones(batch_size, 2), torch.zeros(batch_size, 2))
    
    prob = compute_magnitude_only_probability(c1, c2)
    
    # All should be 0.5 (equal magnitudes)
    expected = torch.tensor([0.5, 0.5, 0.5])
    
    assert torch.allclose(prob, expected, atol=1e-5), \
        f"Expected {expected}, got {prob}"


def test_magnitude_only_no_phase_interaction():
    """
    Verify that phase changes do not affect magnitude-only probability.
    This is the key difference from quantum interference.
    """
    # Base case: both vectors with magnitude 1
    c1_base = torch.complex(torch.tensor([1.0, 0.0]), torch.zeros(2))
    c2_base = torch.complex(torch.tensor([1.0, 0.0]), torch.zeros(2))
    
    prob_base = compute_magnitude_only_probability(c1_base.unsqueeze(0), c2_base.unsqueeze(0))
    
    # Rotate c2 by 90 degrees (pi/2)
    c2_rotated = torch.complex(
        torch.tensor([0.0, 1.0]), 
        torch.zeros(2)
    )
    
    prob_rotated = compute_magnitude_only_probability(c1_base.unsqueeze(0), c2_rotated.unsqueeze(0))
    
    # Magnitudes are the same, so probabilities should be identical
    assert torch.allclose(prob_base, prob_rotated, atol=1e-5), \
        "Magnitude-only should be invariant to phase rotation"


def test_magnitude_only_real_vectors():
    """
    Test that magnitude-only works correctly with purely real vectors
    (imaginary part = 0).
    """
    c1 = torch.complex(torch.tensor([3.0, 4.0]), torch.zeros(2))
    c2 = torch.complex(torch.tensor([5.0, 0.0]), torch.zeros(2))
    
    prob = compute_magnitude_only_probability(c1.unsqueeze(0), c2.unsqueeze(0))
    
    # ||c1||^2 = 9 + 16 = 25
    # ||c2||^2 = 25 + 0 = 25
    # Sum = 50, P(c1) = 25/50 = 0.5
    expected = torch.tensor([0.5])
    
    assert torch.allclose(prob, expected, atol=1e-5), \
        f"Expected {expected}, got {prob}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])