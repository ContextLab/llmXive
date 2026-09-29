"""
Tests for the hamiltonian module.

Specifically verifies T003 requirement: coupling range and positivity.
"""

import pytest
import numpy as np
from scipy.sparse import csr_matrix

from code.hamiltonian import generate_xxz_hamiltonian, get_coupling_distribution_stats
from code.config import ConfigError

def test_coupling_range():
    """
    Verify that for a given delta, all generated couplings J_i satisfy:
    J_i > 0 (strictly positive) when delta < 1.
    
    This test implements the verification requirement for T003:
    "Verify via test_hamiltonian.py::test_coupling_range which asserts all J_i > 0 for delta < 1."
    """
    L = 10
    delta = 0.5  # delta < 1, so lower bound = 1 - 0.5 = 0.5 > 0
    
    # Generate a large number of samples to ensure statistical confidence
    mean, std, min_val, max_val = get_coupling_distribution_stats(delta, n_samples=100000, seed=42)
    
    # Assert that the minimum sampled coupling is strictly positive
    assert min_val > 0.0, f"Min coupling {min_val} is not > 0 for delta={delta}"
    
    # Verify the theoretical bounds
    expected_lower = 1.0 - delta
    expected_upper = 1.0 + delta
    
    assert min_val >= expected_lower - 1e-6, f"Min {min_val} < expected lower {expected_lower}"
    assert max_val <= expected_upper + 1e-6, f"Max {max_val} > expected upper {expected_upper}"

def test_hamiltonian_structure():
    """
    Verify the structure of the generated Hamiltonian matrix.
    """
    L = 4
    delta = 0.2
    seed = 12345
    
    H = generate_xxz_hamiltonian(L, delta, seed=seed)
    
    # Check dimensions
    expected_dim = 2**L
    assert H.shape == (expected_dim, expected_dim)
    
    # Check that it is a sparse matrix
    assert isinstance(H, csr_matrix)
    
    # Check that the matrix is Hermitian (real symmetric in this case since couplings are real)
    # We check H == H.T (transpose) for real symmetric, or H.H == H for Hermitian
    # Since we use complex128 but real inputs, we check closeness
    diff = H - H.T
    # Convert to dense for checking (small L=4 is 16x16)
    diff_dense = diff.toarray()
    assert np.allclose(diff_dense, np.zeros_like(diff_dense)), "Hamiltonian is not symmetric"

def test_invalid_inputs():
    """
    Verify that invalid inputs raise ConfigError.
    """
    # L < 2
    with pytest.raises(ConfigError):
        generate_xxz_hamiltonian(1, 0.5)
    
    # delta out of bounds
    with pytest.raises(ConfigError):
        generate_xxz_hamiltonian(4, 1.5)
    
    with pytest.raises(ConfigError):
        generate_xxz_hamiltonian(4, -0.1)

def test_determinism():
    """
    Verify that the same seed produces the same Hamiltonian.
    """
    L = 6
    delta = 0.3
    seed = 999
    
    H1 = generate_xxz_hamiltonian(L, delta, seed=seed)
    H2 = generate_xxz_hamiltonian(L, delta, seed=seed)
    
    # Compare dense arrays (L=6 -> 64x64 is manageable)
    assert np.allclose(H1.toarray(), H2.toarray()), "Same seed should produce same Hamiltonian"

def test_coupling_positivity_edge_case():
    """
    Edge case: delta = 1.0 -> lower bound = 0.0.
    We expect couplings to be >= 0, but strictly > 0 is not guaranteed by uniform distribution.
    However, the task requires J_i > 0 for delta < 1.
    """
    delta = 0.99
    mean, std, min_val, max_val = get_coupling_distribution_stats(delta, n_samples=100000, seed=42)
    assert min_val > 0.0, f"Min coupling {min_val} is not > 0 for delta={delta}"