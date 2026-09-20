"""
Unit tests for entropy.py (T005 verification)

Tests:
- test_entropy_calc: Verify von Neumann entropy calculation for a known state.
- test_edge_entropy: Verify entropy at l=1 and l=L-1.
- test_batch_computation: Verify batch computation across all cuts.
- test_scaling_ansatz: Verify the scaling ansatz verification function.
"""

import numpy as np
import pytest
from scipy.sparse import csr_matrix, kron, identity

from code.entropy import (
    EntropyError,
    compute_entanglement_entropy,
    compute_entanglement_entropy_batch,
    get_entropy_statistics,
    verify_scaling_ansatz
)


def create_bell_state_2qubits():
    """
    Create a Bell state |Phi+> = (|00> + |11>) / sqrt(2).
    For a 2-qubit system, the entropy of one qubit should be ln(2).
    """
    psi = np.zeros(4)
    psi[0] = 1 / np.sqrt(2)  # |00>
    psi[3] = 1 / np.sqrt(2)  # |11>
    return psi


def create_product_state_2qubits():
    """
    Create a product state |00>. Entropy should be 0.
    """
    psi = np.zeros(4)
    psi[0] = 1.0
    return psi


def create_random_state(L):
    """
    Create a random normalized state vector for L qubits.
    """
    psi = np.random.randn(2 ** L) + 1j * np.random.randn(2 ** L)
    psi = psi / np.linalg.norm(psi)
    return psi


class TestEntropyCalculation:
    """Test basic entropy calculation (FR-004)."""

    def test_bell_state_entropy(self):
        """
        Test that a Bell state gives entropy ln(2) for one qubit.
        This verifies the core entropy calculation.
        """
        psi = create_bell_state_2qubits()
        L = 2
        l = 1  # Cut after first qubit

        entropy = compute_entanglement_entropy(psi, L, l)

        # Expected: S = ln(2) ≈ 0.693
        expected = np.log(2)
        assert np.isclose(entropy, expected, atol=1e-6), \
            f"Expected {expected}, got {entropy}"

    def test_product_state_zero_entropy(self):
        """
        Test that a product state gives zero entropy.
        """
        psi = create_product_state_2qubits()
        L = 2
        l = 1

        entropy = compute_entanglement_entropy(psi, L, l)

        assert np.isclose(entropy, 0.0, atol=1e-6), \
            f"Expected 0.0, got {entropy}"

    def test_invalid_cut_size(self):
        """Test that invalid cut sizes raise EntropyError."""
        psi = create_bell_state_2qubits()
        L = 2

        # l must be in (0, L)
        with pytest.raises(EntropyError):
            compute_entanglement_entropy(psi, L, 0)

        with pytest.raises(EntropyError):
            compute_entanglement_entropy(psi, L, 2)

    def test_wrong_psi_shape(self):
        """Test that wrong psi shape raises EntropyError."""
        psi_wrong = np.array([1.0, 1.0])  # Should be length 4 for L=2
        L = 2

        with pytest.raises(EntropyError):
            compute_entanglement_entropy(psi_wrong, L, 1)


class TestBatchComputation:
    """Test batch entropy computation."""

    def test_batch_all_cuts(self):
        """
        Test computing entropy for all cuts in a small system.
        """
        # Use a 4-qubit Bell-like state: (|0000> + |1111>)/sqrt(2)
        psi = np.zeros(16)
        psi[0] = 1 / np.sqrt(2)
        psi[15] = 1 / np.sqrt(2)
        L = 4

        results = compute_entanglement_entropy_batch(psi, L)

        # Should have cuts 1, 2, 3
        assert 1 in results
        assert 2 in results
        assert 3 in results

        # Entropy should be ln(2) for all cuts in this GHZ-like state
        expected = np.log(2)
        for l, ent in results.items():
            assert np.isclose(ent, expected, atol=1e-5), \
                f"Cut {l}: expected {expected}, got {ent}"

    def test_batch_custom_cuts(self):
        """Test computing entropy for specific cuts."""
        psi = create_random_state(4)
        L = 4
        cuts = [1, 3]

        results = compute_entanglement_entropy_batch(psi, L, cuts=cuts)

        assert set(results.keys()) == set(cuts)


class TestEdgeEntropy:
    """Test edge entropy calculation (l=1, l=L-1)."""

    def test_left_edge_entropy(self):
        """Test entropy at l=1 (left edge)."""
        psi = create_random_state(4)
        L = 4
        entropy = compute_entanglement_entropy(psi, L, 1)
        assert entropy >= 0.0

    def test_right_edge_entropy(self):
        """Test entropy at l=L-1 (right edge)."""
        psi = create_random_state(4)
        L = 4
        entropy = compute_entanglement_entropy(psi, L, 3)
        assert entropy >= 0.0

    def test_edge_symmetry(self):
        """
        Test that S(l) = S(L-l) for a pure state.
        This is a fundamental property of entanglement entropy.
        """
        psi = create_random_state(6)
        L = 6

        for l in range(1, L):
            s_l = compute_entanglement_entropy(psi, L, l)
            s_sym = compute_entanglement_entropy(psi, L, L - l)
            assert np.isclose(s_l, s_sym, atol=1e-10), \
                f"S({l}) = {s_l} != S({L-l}) = {s_sym}"


class TestEntropyStatistics:
    """Test statistics computation over multiple realizations."""

    def test_statistics_computation(self):
        """Test mean, std, min, max computation."""
        # Simulate data from 3 realizations
        entropy_data = {
            1: [0.5, 0.6, 0.7],
            2: [1.0, 1.1, 0.9],
            3: [0.5, 0.6, 0.7]  # Symmetric to l=1
        }

        stats = get_entropy_statistics(entropy_data)

        assert 'mean' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'cuts' in stats

        # Check mean for l=1
        assert np.isclose(stats['mean'][0], 0.6, atol=1e-6)
        # Check std for l=1
        assert np.isclose(stats['std'][0], np.std([0.5, 0.6, 0.7]), atol=1e-6)


class TestScalingAnsatz:
    """Test scaling ansatz verification."""

    def test_logarithmic_scaling(self):
        """
        Test that logarithmic scaling is detected correctly.
        Simulate S(l) = 0.5 * log(l) + 0.1
        """
        cuts = [2, 4, 8, 16, 32]
        entropies = [0.5 * np.log(l) + 0.1 for l in cuts]

        result = verify_scaling_ansatz(cuts, entropies)

        # Slope should be close to 0.5
        assert np.isclose(result['log_slope'], 0.5, atol=0.01), \
            f"Expected slope ~0.5, got {result['log_slope']}"
        # R^2 should be close to 1
        assert result['log_r2'] > 0.99

    def test_constant_scaling(self):
        """
        Test that constant scaling (area law) is detected.
        Simulate S(l) = 1.0 (constant)
        """
        cuts = [2, 4, 8, 16, 32]
        entropies = [1.0] * len(cuts)

        result = verify_scaling_ansatz(cuts, entropies)

        # Constant value should be 1.0
        assert np.isclose(result['const_value'], 1.0, atol=1e-6)
        # R^2 for constant model should be 1.0
        assert result['const_r2'] > 0.99

    def test_insufficient_data(self):
        """Test that insufficient data returns NaN."""
        cuts = [2]
        entropies = [0.5]

        result = verify_scaling_ansatz(cuts, entropies)

        assert np.isnan(result['log_slope'])
        assert np.isnan(result['const_value'])
