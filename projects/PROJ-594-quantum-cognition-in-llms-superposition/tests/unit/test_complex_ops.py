import torch
import pytest
import sys
import os

# Add the project root to the path so we can import code.utils.complex_ops
# The test runner is expected to run from the project root or this script adjusts accordingly.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.complex_ops import interference_cross_term, born_rule, vector_add, to_complex

def test_destructive_interference():
    """
    Test for destructive interference: c1=1, c2=-1 -> P=0 (or very close to 0).
    
    In the quantum formalism:
    c1 = 1 + 0j
    c2 = -1 + 0j
    Sum = 0
    |Sum|^2 = 0
    
    The interference cross-term is 2 * Re(c1 * c2.conj())
    c1 * c2.conj() = 1 * (-1) = -1
    Cross-term = -2
    
    Total probability (unnormalized) = |c1|^2 + |c2|^2 + Cross-term
    = 1 + 1 - 2 = 0
    """
    # Setup: Define two complex amplitudes that should destructively interfere
    # Using torch.complex64 as per project standard
    c1 = torch.tensor([1.0 + 0.0j], dtype=torch.complex64)
    c2 = torch.tensor([-1.0 + 0.0j], dtype=torch.complex64)
    
    # Calculate the cross-term
    cross_term = interference_cross_term(c1, c2)
    
    # Calculate individual magnitudes squared (Born rule for single paths)
    p1 = born_rule(c1)
    p2 = born_rule(c2)
    
    # Theoretical total probability before normalization
    # P_total = |c1|^2 + |c2|^2 + 2*Re(c1*c2*)
    #         = 1 + 1 + (-2) = 0
    p_total = p1 + p2 + cross_term
    
    # Assert that the cross-term is negative (indicating destructive interference)
    assert cross_term < 0, f"Expected negative cross-term for destructive interference, got {cross_term}"
    
    # Assert that the total unnormalized probability is effectively zero
    # Using a small epsilon for floating point tolerance
    assert torch.abs(p_total) < 1e-6, f"Expected total probability ~0 for destructive interference, got {p_total}"

def test_constructive_interference():
    """
    Test for constructive interference: c1=1, c2=1 -> Max probability.
    
    c1 = 1 + 0j
    c2 = 1 + 0j
    Sum = 2
    |Sum|^2 = 4
    
    Cross-term = 2 * Re(1 * 1) = 2
    Total = 1 + 1 + 2 = 4
    
    After softmax normalization (P_final = exp(P_raw) / (exp(P_raw) + exp(P_alt))),
    if we treat the constructive path as the only path (or the dominant one against a zero path),
    the probability approaches 1. Specifically, if P_alt = 0 (no interference),
    P_final = exp(4) / (exp(4) + exp(0)) which is high.
    However, the task description specifically notes c1=1, c2=1 -> P=1 after softmax.
    This implies a comparison where the constructive interference creates the sole significant amplitude.
    
    We verify the raw probability sum is maximized (4.0) and that the cross-term is positive.
    """
    c1 = torch.tensor([1.0 + 0.0j], dtype=torch.complex64)
    c2 = torch.tensor([1.0 + 0.0j], dtype=torch.complex64)
    
    cross_term = interference_cross_term(c1, c2)
    p1 = born_rule(c1)
    p2 = born_rule(c2)
    p_total = p1 + p2 + cross_term
    
    # Assert cross-term is positive (constructive)
    assert cross_term > 0, f"Expected positive cross-term for constructive interference, got {cross_term}"
    
    # Assert total raw probability is 4 (1+1+2)
    assert torch.abs(p_total - 4.0) < 1e-6, f"Expected total probability 4 for constructive interference, got {p_total}"
    
    # Simulate the softmax step described in the task:
    # If we have two outcomes: Constructive (P=4) and a baseline/alternative (P=0 or similar)
    # The prompt says "c1=1, c2=1 -> P=1 after softmax".
    # This holds if the alternative path has 0 probability (or is negligible).
    # Let's verify the softmax logic explicitly.
    p_constructive = p_total
    p_alternative = torch.tensor(0.0, dtype=torch.float32) # Baseline with no superposition
    
    probs = torch.softmax(torch.tensor([p_constructive, p_alternative]), dim=0)
    # The probability of the constructive state should be very close to 1.0
    assert probs[0] > 0.99, f"Expected softmax probability ~1.0 for constructive case, got {probs[0]}"

def test_interference_vector_batch():
    """
    Test interference on batched tensors to ensure vectorization works correctly.
    """
    # Batch of 4: [Destructive, Constructive, Partial Destructive, Partial Constructive]
    c1_vals = torch.tensor([1.0, 1.0, 1.0, 1.0], dtype=torch.complex64)
    c2_vals = torch.tensor([-1.0, 1.0, -0.5, 0.5], dtype=torch.complex64)
    
    cross_terms = interference_cross_term(c1_vals, c2_vals)
    
    # Expected:
    # 1. 2 * Re(1 * -1) = -2
    # 2. 2 * Re(1 * 1) = 2
    # 3. 2 * Re(1 * -0.5) = -1
    # 4. 2 * Re(1 * 0.5) = 1
    expected = torch.tensor([-2.0, 2.0, -1.0, 1.0], dtype=torch.float32)
    
    assert torch.allclose(cross_terms, expected, atol=1e-6), f"Batch interference mismatch: {cross_terms} vs {expected}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])