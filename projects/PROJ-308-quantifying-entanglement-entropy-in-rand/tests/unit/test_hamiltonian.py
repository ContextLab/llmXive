"""
Unit tests for Hamiltonian generation (T003).

Verifies:
- Coupling range validation (FR-002)
- Correctness of Hamiltonian construction for small systems
"""

import numpy as np
import pytest
from scipy.sparse import csr_matrix
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from config import ConfigError
from hamiltonian import generate_xxz_hamiltonian, get_coupling_distribution_stats


class TestCouplingRange:
    """Test FR-002: Random couplings J_i ~ U[1-delta, 1+delta]"""

    def test_coupling_range(self):
        """Verify that couplings are within [1-delta, 1+delta]"""
        L = 10
        delta = 0.2
        seed = 42
        
        # Run multiple times to ensure all couplings are in range
        for _ in range(10):
            H = generate_xxz_hamiltonian(L, delta, seed=seed)
            mean, std, min_val, max_val = get_coupling_distribution_stats(delta, n_samples=10000, seed=seed)
            
            # Theoretical bounds
            lower_bound = 1.0 - delta
            upper_bound = 1.0 + delta
            
            assert min_val >= lower_bound - 1e-10, f"Min coupling {min_val} < {lower_bound}"
            assert max_val <= upper_bound + 1e-10, f"Max coupling {max_val} > {upper_bound}"
            
            # Mean should be close to 1.0
            assert np.isclose(mean, 1.0, atol=0.01), f"Mean {mean} != 1.0"

    def test_delta_zero(self):
        """Test uniform coupling when delta=0"""
        L = 10
        delta = 0.0
        seed = 123
        
        H = generate_xxz_hamiltonian(L, delta, seed=seed)
        mean, std, min_val, max_val = get_coupling_distribution_stats(delta, n_samples=1000, seed=seed)
        
        assert np.isclose(std, 0.0, atol=1e-10), "Std should be 0 for delta=0"
        assert np.isclose(min_val, 1.0), "Min should be 1.0"
        assert np.isclose(max_val, 1.0), "Max should be 1.0"

    def test_delta_one(self):
        """Test maximum disorder when delta=1"""
        L = 10
        delta = 1.0
        seed = 456
        
        H = generate_xxz_hamiltonian(L, delta, seed=seed)
        mean, std, min_val, max_val = get_coupling_distribution_stats(delta, n_samples=10000, seed=seed)
        
        assert min_val >= 0.0, "Min coupling should be >= 0"
        assert max_val <= 2.0, "Max coupling should be <= 2.0"

    def test_invalid_delta_negative(self):
        """Test that negative delta raises ConfigError"""
        with pytest.raises(ConfigError):
            generate_xxz_hamiltonian(10, delta=-0.1, seed=42)

    def test_invalid_delta_too_large(self):
        """Test that delta > 1 raises ConfigError"""
        with pytest.raises(ConfigError):
            generate_xxz_hamiltonian(10, delta=1.5, seed=42)

    def test_invalid_L_small(self):
        """Test that L < 2 raises ConfigError"""
        with pytest.raises(ConfigError):
            generate_xxz_hamiltonian(1, delta=0.2, seed=42)


class TestHamiltonianConstruction:
    """Test correctness of Hamiltonian matrix construction"""

    def test_hamiltonian_shape(self):
        """Verify Hamiltonian has correct shape (2^L x 2^L)"""
        L = 4
        delta = 0.2
        seed = 42
        
        H = generate_xxz_hamiltonian(L, delta, seed=seed)
        
        assert isinstance(H, csr_matrix), "H should be a sparse matrix"
        assert H.shape == (2**L, 2**L), f"Shape should be ({2**L}, {2**L})"

    def test_hermiticity(self):
        """Verify Hamiltonian is Hermitian"""
        L = 6
        delta = 0.3
        seed = 789
        
        H = generate_xxz_hamiltonian(L, delta, seed=seed)
        
        # Convert to dense for small L to check hermiticity
        H_dense = H.toarray()
        assert np.allclose(H_dense, H_dense.conj().T), "H should be Hermitian"

    def test_reproducibility(self):
        """Verify same seed produces same Hamiltonian"""
        L = 5
        delta = 0.2
        seed = 12345
        
        H1 = generate_xxz_hamiltonian(L, delta, seed=seed)
        H2 = generate_xxz_hamiltonian(L, delta, seed=seed)
        
        assert np.allclose(H1.toarray(), H2.toarray()), "Same seed should produce same H"

    def test_trace_zero_for_xxz(self):
        """
        The trace of XXZ Hamiltonian is not necessarily zero, but for a symmetric
        distribution of couplings around 1, the expected trace should be computable.
        For L=2, H = J/4 * (sigma_x sigma_x + sigma_y sigma_y + sigma_z sigma_z)
        Trace of each term is 0, so trace(H) = 0.
        """
        L = 2
        delta = 0.0  # J=1
        seed = 42
        
        H = generate_xxz_hamiltonian(L, delta, seed=seed)
        H_dense = H.toarray()
        
        # Trace should be 0 for L=2, delta=0
        trace = np.trace(H_dense)
        assert np.isclose(trace, 0.0, atol=1e-10), f"Trace should be 0, got {trace}"
