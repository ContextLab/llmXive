import numpy as np
import pytest
from pathlib import Path
from code.permutation import generate_zero_preserving_permutations, compute_batched_autocorrelations

def test_zero_preserving_logic():
    """Verify that zero positions are fixed and signs are shuffled."""
    window = np.array([1, 0, -1, 0, 1], dtype=np.int8)
    n_perms = 10
    seed = 42
    perms = generate_zero_preserving_permutations(window, n_perms, seed)
    
    assert perms.shape == (n_perms, 5)
    for p in perms:
        # Zeros must stay at indices 1 and 3
        assert p[1] == 0 and p[3] == 0
        # Non-zeros must be at 0, 2, 4
        assert p[0] != 0 and p[2] != 0 and p[4] != 0
        # Global counts must be preserved (two 1s, one -1)
        assert np.sum(p == 1) == 2
        assert np.sum(p == -1) == 1

def test_batched_autocorr_shape():
    """Verify the output shape of the batched FFT autocorrelation."""
    L = 1000
    n_seq = 5
    seqs = np.random.choice([-1, 0, 1], size=(n_seq, L)).astype(np.int8)
    res = compute_batched_autocorrelations(seqs, L)
    assert res.shape == (n_seq, L // 2)

def test_p_value_clamping_logic():
    """
    Test the p-value calculation logic used in the main loop.
    p = (count + 1) / 1001.
    """
    # Mocking the loop logic
    def calc_p(obs, null_vals):
        count = np.sum(np.abs(null_vals) >= np.abs(obs))
        p = (count + 1) / 1001
        return max(0.001, min(0.999, p))

    # Case 1: All nulls are smaller than obs -> count = 0 -> p = 1/1001 approx 0.000999 -> clamp to 0.001
    obs_extreme = 1.0
    null_small = np.zeros(1000)
    assert calc_p(obs_extreme, null_small) == 0.001

    # Case 2: All nulls are larger than obs -> count = 1000 -> p = 1001/1001 = 1.0 -> clamp to 0.999
    obs_tiny = 0.0
    null_large = np.ones(1000)
    assert calc_p(obs_tiny, null_large) == 0.999

    # Case 3: Half are larger -> count = 500 -> p = 501/1001 approx 0.5 -> no clamp
    obs_mid = 0.5
    null_mid = np.array([0.6]*500 + [0.4]*500)
    p_mid = calc_p(obs_mid, null_mid)
    assert 0.49 < p_mid < 0.51