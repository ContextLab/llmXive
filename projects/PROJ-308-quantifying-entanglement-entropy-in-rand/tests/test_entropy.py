"""
Unit tests for entanglement entropy computation module.

Tests FR-004: Compute von Neumann entropy S(l) for all bipartitions.
"""

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from entropy import (
    compute_entanglement_entropy,
    compute_entanglement_entropy_batch,
    get_entropy_statistics,
    EntropyError,
    _compute_reduced_density_matrix,
    _compute_von_neumann_entropy
)


class TestReducedDensityMatrix:
    """Tests for reduced density matrix computation."""

    def test_valid_bipartition(self):
        """Test that valid bipartition cuts work correctly."""
        # Create a simple product state: |0000>
        L = 4
        psi = np.zeros(2 ** L)
        psi[0] = 1.0  # |0000>

        rho = _compute_reduced_density_matrix(psi, L, l=2)
        assert rho.shape == (4, 4)  # 2^2 x 2^2

    def test_invalid_bipartition_low(self):
        """Test that l=0 raises an error."""
        L = 4
        psi = np.zeros(2 ** L)
        psi[0] = 1.0

        with pytest.raises(EntropyError):
            _compute_reduced_density_matrix(psi, L, l=0)

    def test_invalid_bipartition_high(self):
        """Test that l=L raises an error."""
        L = 4
        psi = np.zeros(2 ** L)
        psi[0] = 1.0

        with pytest.raises(EntropyError):
            _compute_reduced_density_matrix(psi, L, l=L)


class TestVonNeumannEntropy:
    """Tests for von Neumann entropy computation."""

    def test_product_state_zero_entropy(self):
        """Product states should have zero entanglement entropy."""
        # |00> state, bipartition at l=1
        L = 2
        psi = np.zeros(2 ** L)
        psi[0] = 1.0  # |00>

        rho = _compute_reduced_density_matrix(psi, L, l=1)
        S = _compute_von_neumann_entropy(rho)
        assert np.isclose(S, 0.0, atol=1e-10)

    def test_maximally_entangled_state(self):
        """Bell state should have entropy = 1 bit."""
        # |00> + |11> (normalized)
        L = 2
        psi = np.zeros(2 ** L)
        psi[0] = 1.0 / np.sqrt(2)
        psi[3] = 1.0 / np.sqrt(2)

        rho = _compute_reduced_density_matrix(psi, L, l=1)
        S = _compute_von_neumann_entropy(rho)
        assert np.isclose(S, 1.0, atol=1e-6)

    def test_random_state_positive_entropy(self):
        """Random state should have positive entropy."""
        L = 4
        psi = np.random.randn(2 ** L) + 1j * np.random.randn(2 ** L)
        psi = psi / np.linalg.norm(psi)

        rho = _compute_reduced_density_matrix(psi, L, l=2)
        S = _compute_von_neumann_entropy(rho)
        assert S > 0.0


class TestComputeEntanglementEntropy:
    """Tests for the main entropy computation function."""

    def test_product_state_all_cuts(self):
        """Product state should have zero entropy at all cuts."""
        L = 4
        psi = np.zeros(2 ** L)
        psi[0] = 1.0  # |0000>

        cuts, entropies, is_unresolved = compute_entanglement_entropy(psi, L)

        assert cuts == [1, 2, 3]
        assert len(entropies) == 3
        assert all(np.isclose(S, 0.0, atol=1e-10) for S in entropies)
        assert not is_unresolved

    def test_invalid_wavefunction_size(self):
        """Wrong wavefunction size should raise an error."""
        L = 4
        psi = np.random.randn(2 ** (L - 1))  # Wrong size

        with pytest.raises(EntropyError):
            compute_entanglement_entropy(psi, L)

    def test_symmetry_for_product_state(self):
        """For product state, entropy should be symmetric around center."""
        L = 6
        psi = np.zeros(2 ** L)
        psi[0] = 1.0

        cuts, entropies, is_unresolved = compute_entanglement_entropy(psi, L)

        # All entropies should be zero
        assert all(np.isclose(S, 0.0, atol=1e-10) for S in entropies)


class TestComputeEntanglementEntropyBatch:
    """Tests for batch entropy computation."""

    def test_batch_computation(self):
        """Test batch computation with multiple realizations."""
        L = 4
        N_real = 3

        # Create product states
        psi_list = []
        for _ in range(N_real):
            psi = np.zeros(2 ** L)
            psi[0] = 1.0
            psi_list.append(psi)

        L_list = [L] * N_real
        delta = 0.0
        realization_ids = [1, 2, 3]

        result = compute_entanglement_entropy_batch(psi_list, L_list, delta, realization_ids)

        assert 'cuts' in result
        assert result['cuts'] == [1, 2, 3]
        assert 'entropies' in result
        assert result['entropies'].shape == (N_real, L - 1)
        assert 'unresolved_ids' in result
        assert len(result['unresolved_ids']) == 0
        assert 'metadata' in result
        assert result['metadata']['L'] == L
        assert result['metadata']['delta'] == delta

    def test_batch_with_unresolved(self):
        """Test batch computation with some unresolved realizations."""
        L = 4
        N_real = 3

        # First two are valid, third has wrong size
        psi_list = []
        for i in range(N_real):
            if i < 2:
                psi = np.zeros(2 ** L)
                psi[0] = 1.0
            else:
                psi = np.zeros(2 ** (L - 1))  # Wrong size
            psi_list.append(psi)

        L_list = [L] * N_real
        delta = 0.0
        realization_ids = [1, 2, 3]

        result = compute_entanglement_entropy_batch(psi_list, L_list, delta, realization_ids)

        assert len(result['unresolved_ids']) == 1
        assert 3 in result['unresolved_ids']
        assert np.any(np.isnan(result['entropies'][2, :]))

    def test_mismatched_lengths(self):
        """Test that mismatched input lengths raise an error."""
        psi_list = [np.zeros(16), np.zeros(16)]
        L_list = [4, 4, 4]  # Too many
        delta = 0.0
        realization_ids = [1, 2]

        with pytest.raises(EntropyError):
            compute_entanglement_entropy_batch(psi_list, L_list, delta, realization_ids)


class TestGetEntropyStatistics:
    """Tests for entropy statistics computation."""

    def test_statistics_computation(self):
        """Test mean, std, min, max computation."""
        L = 4
        N_real = 5

        # Create entropies with known statistics
        entropies = np.array([
            [0.0, 0.5, 0.0],
            [0.0, 0.5, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.5, 0.0],
            [0.0, 0.5, 0.0]
        ])

        stats = get_entropy_statistics(entropies)

        assert 'mean' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats

        # Check mean for middle cut (should be 0.6)
        assert np.isclose(stats['mean'][1], 0.6, atol=1e-6)

    def test_statistics_with_nan(self):
        """Test that NaN values are handled correctly."""
        entropies = np.array([
            [0.0, 0.5, 0.0],
            [np.nan, np.nan, np.nan],  # Unresolved
            [0.0, 1.0, 0.0]
        ])

        stats = get_entropy_statistics(entropies)

        # Should compute stats only from valid rows
        assert np.all(np.isfinite(stats['mean']))
        assert stats['mean'][1] == 0.75  # (0.5 + 1.0) / 2

    def test_all_nan(self):
        """Test when all values are NaN."""
        entropies = np.array([
            [np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan]
        ])

        stats = get_entropy_statistics(entropies)

        assert np.all(np.isnan(stats['mean']))
        assert np.all(np.isnan(stats['std']))