"""
Unit tests for code/generate_hamiltonian.py (T005).
"""

import numpy as np
import pytest

from code.generate_hamiltonian import generate_hamiltonian, generate_hamiltonian_batch


class TestGenerateHamiltonian:
    """Tests for the generate_hamiltonian function."""

    def test_shape(self):
        """Test that the output matrix has the correct shape."""
        L = 10
        H, epsilons = generate_hamiltonian(L, W=1.0, seed=0)
        assert H.shape == (L, L)
        assert epsilons.shape == (L,)

    def test_symmetry(self):
        """Test that the Hamiltonian is symmetric (Hermitian)."""
        H, _ = generate_hamiltonian(L=50, W=2.0, seed=123)
        assert np.allclose(H, H.T)

    def test_diagonal_is_epsilons(self):
        """Test that the diagonal elements match the generated epsilons."""
        L = 20
        H, epsilons = generate_hamiltonian(L, W=1.5, seed=42)
        assert np.allclose(np.diag(H), epsilons)

    def test_off_diagonal_hopping(self):
        """Test that off-diagonal elements are -t (nearest neighbors)."""
        L = 10
        t = 1.0
        H, _ = generate_hamiltonian(L, W=0.0, seed=0, t=t)

        # Check super-diagonal
        super_diag = np.diag(H, k=1)
        assert np.allclose(super_diag, -t)

        # Check sub-diagonal
        sub_diag = np.diag(H, k=-1)
        assert np.allclose(sub_diag, -t)

    def test_non_neighbors_zero(self):
        """Test that non-nearest neighbors are zero."""
        L = 10
        H, _ = generate_hamiltonian(L, W=0.0, seed=0)

        # Check elements with distance > 1
        for i in range(L):
            for j in range(L):
                if abs(i - j) > 1:
                    assert H[i, j] == 0.0

    def test_disorder_range(self):
        """Test that epsilons are within [-W/2, W/2]."""
        L = 100
        W = 2.0
        H, epsilons = generate_hamiltonian(L, W=W, seed=999)

        lower_bound = -W / 2.0
        upper_bound = W / 2.0

        assert np.all(epsilons >= lower_bound)
        assert np.all(epsilons <= upper_bound)

    def test_zero_disorder(self):
        """Test that W=0 results in zero on-site energies."""
        L = 10
        H, epsilons = generate_hamiltonian(L, W=0.0, seed=0)
        assert np.allclose(epsilons, 0.0)

    def test_custom_hopping(self):
        """Test that custom hopping parameter t is respected."""
        L = 10
        t_custom = 2.5
        H, _ = generate_hamiltonian(L, W=0.0, seed=0, t=t_custom)

        super_diag = np.diag(H, k=1)
        assert np.allclose(super_diag, -t_custom)

    def test_reproducibility(self):
        """Test that the same seed produces the same result."""
        L = 10
        W = 1.0
        seed = 12345

        H1, eps1 = generate_hamiltonian(L, W, seed)
        H2, eps2 = generate_hamiltonian(L, W, seed)

        assert np.array_equal(H1, H2)
        assert np.array_equal(eps1, eps2)

    def test_invalid_L(self):
        """Test that invalid L raises ValueError."""
        with pytest.raises(ValueError):
            generate_hamiltonian(0, W=1.0, seed=0)
        with pytest.raises(ValueError):
            generate_hamiltonian(-5, W=1.0, seed=0)

    def test_invalid_W(self):
        """Test that invalid W raises ValueError."""
        with pytest.raises(ValueError):
            generate_hamiltonian(10, W=-1.0, seed=0)


class TestGenerateHamiltonianBatch:
    """Tests for the generate_hamiltonian_batch function."""

    def test_batch_shape(self):
        """Test batch output shapes."""
        L = 10
        num_realizations = 5
        H_batch, eps_batch = generate_hamiltonian_batch(L, W=1.0, num_realizations=num_realizations, base_seed=0)

        assert H_batch.shape == (num_realizations, L, L)
        assert eps_batch.shape == (num_realizations, L)

    def test_batch_consistency(self):
        """Test that batch results match individual calls."""
        L = 10
        W = 1.0
        num_realizations = 3
        base_seed = 100

        H_batch, eps_batch = generate_hamiltonian_batch(L, W, num_realizations, base_seed)

        for i in range(num_realizations):
            H_ind, eps_ind = generate_hamiltonian(L, W, base_seed + i)
            assert np.array_equal(H_batch[i], H_ind)
            assert np.array_equal(eps_batch[i], eps_ind)
