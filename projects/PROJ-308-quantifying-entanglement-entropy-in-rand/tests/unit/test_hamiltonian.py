"""
Unit tests for hamiltonian.py

Verifies FR-002: XXZ Heisenberg Hamiltonian with random nearest-neighbour couplings.
Specifically tests the coupling range U[-delta, 1+delta].
"""

import pytest
import numpy as np
from scipy.sparse import csr_matrix

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from hamiltonian import generate_xxz_hamiltonian, get_coupling_distribution_stats
from config import ConfigError

class TestHamiltonianCouplingRange:
    """Tests for T003: Verify coupling range U[-delta, 1+delta]."""

    def test_coupling_range(self):
        """
        Verify that generated couplings fall within U[-delta, 1+delta].
        
        This is the core verification for T003. We run the distribution stats
        function with a fixed seed to ensure reproducibility and check that
        min >= -delta and max <= 1+delta.
        """
        delta = 0.5
        seed = 42
        n_samples = 100000
        
        mean, std, min_val, max_val = get_coupling_distribution_stats(
            delta=delta, 
            n_samples=n_samples, 
            seed=seed
        )
        
        # Theoretical bounds
        lower_bound = -delta
        upper_bound = 1.0 + delta
        
        # Allow small numerical tolerance for floating point comparisons
        tolerance = 1e-9
        
        assert min_val >= lower_bound - tolerance, \
            f"Min coupling {min_val} is below lower bound {lower_bound}"
        assert max_val <= upper_bound + tolerance, \
            f"Max coupling {max_val} is above upper bound {upper_bound}"
        
        # Check that the range is actually being used (not a degenerate case)
        # With 100k samples, we should see values close to the bounds
        assert max_val - min_val > (upper_bound - lower_bound) * 0.99, \
            "Coupling range is not fully utilized"

    def test_coupling_range_zero_delta(self):
        """Test that delta=0 yields constant couplings at 1.0."""
        delta = 0.0
        seed = 123
        
        mean, std, min_val, max_val = get_coupling_distribution_stats(
            delta=delta,
            n_samples=1000,
            seed=seed
        )
        
        # With delta=0, all couplings should be exactly 1.0
        assert abs(mean - 1.0) < 1e-10
        assert abs(std) < 1e-10
        assert abs(min_val - 1.0) < 1e-10
        assert abs(max_val - 1.0) < 1e-10

    def test_coupling_range_max_delta(self):
        """Test that delta=1.0 yields couplings in [-1, 2]."""
        delta = 1.0
        seed = 999
        
        mean, std, min_val, max_val = get_coupling_distribution_stats(
            delta=delta,
            n_samples=100000,
            seed=seed
        )
        
        lower_bound = -1.0
        upper_bound = 2.0
        
        assert min_val >= lower_bound - 1e-9
        assert max_val <= upper_bound + 1e-9

    def test_hamiltonian_shape_and_type(self):
        """Verify the Hamiltonian is a sparse matrix of correct shape."""
        L = 6
        delta = 0.3
        seed = 42
        
        H = generate_xxz_hamiltonian(L=L, delta=delta, seed=seed)
        
        expected_size = 2 ** L
        assert isinstance(H, csr_matrix)
        assert H.shape == (expected_size, expected_size)
        assert H.dtype == np.complex128

    def test_hamiltonian_hermiticity(self):
        """Verify the Hamiltonian is Hermitian (H == H^dagger)."""
        L = 5
        delta = 0.4
        seed = 777
        
        H = generate_xxz_hamiltonian(L=L, delta=delta, seed=seed)
        
        # H should be Hermitian: H = H^dagger
        # For sparse matrices, we check H - H^H is zero
        H_dagger = H.getH()
        diff = H - H_dagger
        
        # Check max absolute difference
        max_diff = diff.max()
        assert max_diff < 1e-10, f"Hamiltonian is not Hermitian: max diff = {max_diff}"

    def test_invalid_L(self):
        """Verify ConfigError is raised for L < 2."""
        with pytest.raises(ConfigError):
            generate_xxz_hamiltonian(L=1, delta=0.5)
        
        with pytest.raises(ConfigError):
            generate_xxz_hamiltonian(L=0, delta=0.5)

    def test_invalid_delta(self):
        """Verify ConfigError is raised for delta out of bounds."""
        with pytest.raises(ConfigError):
            generate_xxz_hamiltonian(L=4, delta=-0.1)
        
        with pytest.raises(ConfigError):
            generate_xxz_hamiltonian(L=4, delta=1.1)

    def test_reproducibility(self):
        """Verify that same seed produces same Hamiltonian."""
        L = 4
        delta = 0.2
        seed = 12345
        
        H1 = generate_xxz_hamiltonian(L=L, delta=delta, seed=seed)
        H2 = generate_xxz_hamiltonian(L=L, delta=delta, seed=seed)
        
        # Check if matrices are identical
        diff = H1 - H2
        assert diff.nnz == 0 or diff.max() < 1e-12, "Same seed should produce same Hamiltonian"

    def test_non_reproducibility_different_seeds(self):
        """Verify that different seeds produce different Hamiltonians."""
        L = 4
        delta = 0.2
        
        H1 = generate_xxz_hamiltonian(L=L, delta=delta, seed=111)
        H2 = generate_xxz_hamiltonian(L=L, delta=delta, seed=222)
        
        # They should be different with high probability
        diff = H1 - H2
        assert diff.nnz > 0 or diff.max() > 1e-12, "Different seeds should produce different Hamiltonians"
