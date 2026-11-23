import torch
import json
import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.loss_utils import compute_interference_cross_term, verify_ambiguous_interference

def test_interference_cross_term_negative_for_ambiguous():
    """
    Test that the interference cross-term can be negative for ambiguous inputs.
    This test simulates ambiguous inputs by creating complex vectors with phase differences
    that result in destructive interference.
    """
    # Create two complex vectors
    # c1 = 1 + 0j
    # c2 = -1 + 0j (phase difference of pi)
    # cross_term = 2 * Re( (1) * conj(-1) ) = 2 * Re(-1) = -2
    c1 = torch.tensor([1.0 + 0j, 2.0 + 0j])
    c2 = torch.tensor([-1.0 + 0j, -2.0 + 0j])
    
    cross_term = compute_interference_cross_term(c1.unsqueeze(0), c2.unsqueeze(0)) # [1, 2]
    expected = torch.tensor([-2.0, -8.0]) # 2*Re(1*-1) = -2, 2*Re(2*-2) = -8
    
    assert torch.allclose(cross_term.squeeze(0), expected), f"Expected {expected}, got {cross_term.squeeze(0)}"
    
    # Verify that at least 10% are negative (here 100% are negative)
    assert verify_ambiguous_interference(cross_term.squeeze(0), threshold=0.0, min_percentage=0.10)

def test_interference_cross_term_positive():
    """
    Test that the interference cross-term can be positive (constructive interference).
    """
    c1 = torch.tensor([1.0 + 0j])
    c2 = torch.tensor([1.0 + 0j])
    
    cross_term = compute_interference_cross_term(c1.unsqueeze(0), c2.unsqueeze(0))
    expected = torch.tensor([2.0]) # 2*Re(1*1) = 2
    
    assert torch.allclose(cross_term.squeeze(0), expected)

def test_verify_ambiguous_interference_threshold():
    """
    Test the verify_ambiguous_interference function with various thresholds.
    """
    # Create a tensor with mixed positive and negative values
    # 2 negative, 3 positive -> 40% negative
    values = torch.tensor([-1.0, -2.0, 1.0, 2.0, 3.0])
    
    # Should pass with min_percentage=0.4
    assert verify_ambiguous_interference(values, threshold=0.0, min_percentage=0.4)
    
    # Should fail with min_percentage=0.5
    assert not verify_ambiguous_interference(values, threshold=0.0, min_percentage=0.5)
    
    # Should fail with 0% negative
    values_all_pos = torch.tensor([1.0, 2.0, 3.0])
    assert not verify_ambiguous_interference(values_all_pos, threshold=0.0, min_percentage=0.10)
    
    # Should pass with 100% negative
    values_all_neg = torch.tensor([-1.0, -2.0, -3.0])
    assert verify_ambiguous_interference(values_all_neg, threshold=0.0, min_percentage=0.10)
