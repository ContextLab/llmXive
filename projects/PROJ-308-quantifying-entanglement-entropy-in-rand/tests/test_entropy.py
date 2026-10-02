"""
Unit tests for the entanglement entropy computation module.

Tests cover:
- Single bipartition entropy calculation
- Batch entropy calculation
- Statistics computation
- Scaling ansatz verification
- Error handling for invalid inputs
"""

import pytest
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.entropy import (
    EntropyError,
    compute_entanglement_entropy,
    compute_entanglement_entropy_batch,
    get_entropy_statistics,
    verify_scaling_ansatz
)


def create_random_ground_state(L: int, seed: int = 42) -> np.ndarray:
    """
    Create a random normalized ground state for testing.

    Parameters
    ----------
    L : int
        System size.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    np.ndarray
        Normalized random state vector of shape (2^L,).
    """
    rng = np.random.default_rng(seed)
    psi = rng.random(2 ** L) + 1j * rng.random(2 ** L)
    psi = psi / np.linalg.norm(psi)
    return psi


def test_entropy_calc():
    """
    Test FR-004: Compute von Neumann entropy S(l) for all bipartitions l.

    Verifies that:
    1. Entropy is computed correctly for a known state.
    2. Entropy is symmetric: S(l) == S(L-l).
    3. Entropy is non-negative.
    4. Entropy is zero for product states.
    """
    # Test 1: Random state entropy calculation
    L = 6
    psi = create_random_ground_state(L, seed=123)

    # Compute entropy for l=3 (middle cut)
    entropy_mid = compute_entanglement_entropy(psi, L, l=3)

    assert entropy_mid >= 0.0, "Entropy must be non-negative"
    assert not np.isnan(entropy_mid), "Entropy should not be NaN for valid input"

    # Test 2: Symmetry S(l) == S(L-l)
    entropy_l2 = compute_entanglement_entropy(psi, L, l=2)
    entropy_l4 = compute_entanglement_entropy(psi, L, l=4)

    assert np.isclose(entropy_l2, entropy_l4, rtol=1e-10), \
        f"Entropy symmetry failed: S(2)={entropy_l2}, S(4)={entropy_l4}"

    # Test 3: Batch computation
    batch_results = compute_entanglement_entropy_batch(psi, L)

    assert len(batch_results) == L - 1, f"Expected {L-1} cuts, got {len(batch_results)}"
    for l, ent in batch_results.items():
        assert 1 <= l < L, f"Invalid cut size {l}"
        assert not np.isnan(ent) or ent is None, "Batch result should be numeric or NaN"

    # Test 4: Product state (zero entanglement)
    # Create a product state: all spins up
    psi_product = np.zeros(2 ** L, dtype=complex)
    psi_product[0] = 1.0  # |00...0> state

    for l in range(1, L):
        ent = compute_entanglement_entropy(psi_product, L, l)
        assert np.isclose(ent, 0.0, atol=1e-12), \
            f"Product state should have zero entropy at l={l}, got {ent}"

    # Test 5: Error handling
    with pytest.raises(EntropyError):
        compute_entanglement_entropy(psi, L, l=0)  # Invalid l

    with pytest.raises(EntropyError):
        compute_entanglement_entropy(psi, L, l=L)  # Invalid l

    with pytest.raises(EntropyError):
        compute_entanglement_entropy(psi, L, l=3, method="invalid")  # Invalid method

    # Wrong dimension
    wrong_psi = np.random.random(2 ** (L - 1))
    with pytest.raises(EntropyError):
        compute_entanglement_entropy(wrong_psi, L, l=3)

def test_statistics_computation():
    """Test get_entropy_statistics function."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    stats = get_entropy_statistics(values)

    assert stats['count'] == 5
    assert stats['mean'] == 3.0
    assert stats['min'] == 1.0
    assert stats['max'] == 5.0
    assert stats['std'] == np.std(values)
    assert stats['nan_count'] == 0

    # With NaNs
    values_with_nan = [1.0, np.nan, 3.0, np.nan, 5.0]
    stats_nan = get_entropy_statistics(values_with_nan)

    assert stats_nan['count'] == 3
    assert stats_nan['nan_count'] == 2
    assert stats_nan['mean'] == 3.0

    # All NaN
    all_nan = [np.nan, np.nan]
    stats_all_nan = get_entropy_statistics(all_nan)

    assert stats_all_nan['count'] == 0
    assert np.isnan(stats_all_nan['mean'])

def test_scaling_ansatz_verification():
    """Test verify_scaling_ansatz function."""
    # Generate data following S = 0.5 * log(l) + 0.1
    l_vals = [2, 4, 8, 16, 32]
    s_vals = [0.5 * np.log(l) + 0.1 + np.random.normal(0, 0.01) for l in l_vals]

    result = verify_scaling_ansatz(l_vals, s_vals, model="log")

    assert result['model'] == "log"
    assert result['n_points'] == 5
    assert np.isclose(result['c_eff'], 0.5, atol=0.05)
    assert result['r_squared'] > 0.95

    # Test constant model
    const_s = [2.0, 2.0, 2.0, 2.0]
    result_const = verify_scaling_ansatz(l_vals[:4], const_s, model="const")

    assert result_const['model'] == "const"
    assert np.isclose(result_const['intercept'], 2.0)
    assert result_const['r_squared'] == 1.0

    # Error on insufficient data
    with pytest.raises(EntropyError):
        verify_scaling_ansatz([2], [1.0], model="log")

    # Error on invalid model
    with pytest.raises(EntropyError):
        verify_scaling_ansatz(l_vals, s_vals, model="invalid")

def test_batch_edge_cases():
    """Test batch computation edge cases."""
    L = 4
    psi = create_random_ground_state(L)

    # Custom cuts
    custom_cuts = [1, 3]
    results = compute_entanglement_entropy_batch(psi, L, cuts=custom_cuts)

    assert set(results.keys()) == set(custom_cuts)
    assert len(results) == 2

    # Empty cuts list
    results_empty = compute_entanglement_entropy_batch(psi, L, cuts=[])
    assert results_empty == {}

    # Invalid psi dimension
    wrong_psi = np.random.random(2 ** (L + 1))
    with pytest.raises(EntropyError):
        compute_entanglement_entropy_batch(wrong_psi, L)