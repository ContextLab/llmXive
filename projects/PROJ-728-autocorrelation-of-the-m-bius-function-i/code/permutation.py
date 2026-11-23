"""
permutation.py
----------------

Utilities for generating zero‑preserving sign permutations of a Möbius
window and for computing batched autocorrelations via FFT.

The module originally provided ``generate_zero_preserving_permutations``,
``generate_permutations``, and ``compute_batched_autocorrelations``.
For the null‑distribution stage a helper ``_load_mobius_array`` is also
required; it was missing and caused an import error in ``null_distribution``.
The implementation below adds this missing function while keeping the
existing public API unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np

__all__ = [
    "generate_zero_preserving_permutations",
    "generate_permutations",
    "compute_batched_autocorrelations",
    "main",
    "_load_mobius_array",
]


# ----------------------------------------------------------------------
# Existing public functions (unchanged)
# ----------------------------------------------------------------------
def generate_zero_preserving_permutations(window: np.ndarray, n_permutations: int, seed: int) -> np.ndarray:
    """
    Generate ``n_permutations`` windows that keep zero positions fixed
    and uniformly shuffle the signs of the non‑zero entries.

    Parameters
    ----------
    window : np.ndarray
        1‑D array of length ``L`` containing Möbius values (‑1, 0, 1).
    n_permutations : int
        Number of permutations to generate.
    seed : int
        Seed for the random number generator (ensures reproducibility).

    Returns
    -------
    np.ndarray
        Array of shape ``(n_permutations, L)`` where each row is a
        zero‑preserving permutation of ``window``.
    """
    rng = np.random.default_rng(seed)
    # Identify positions of non‑zero entries.
    nonzero_mask = window != 0
    nonzero_vals = window[nonzero_mask]

    # Pre‑allocate output.
    perms = np.empty((n_permutations, len(window)), dtype=window.dtype)

    for i in range(n_permutations):
        # Shuffle the signs of the non‑zero entries.
        shuffled = rng.permutation(nonzero_vals)
        # Insert shuffled signs back into a copy of the original window.
        perm = np.array(window, copy=True)
        perm[nonzero_mask] = shuffled
        perms[i] = perm
    return perms


# Legacy alias kept for backward compatibility.
def generate_permutations(window: np.ndarray, n_permutations: int, seed: int) -> np.ndarray:
    """Legacy wrapper for :func:`generate_zero_preserving_permutations`."""
    return generate_zero_preserving_permutations(window, n_permutations, seed)


def compute_batched_autocorrelations(sequences: np.ndarray, L: int) -> np.ndarray:
    """
    Compute normalized autocorrelations for all lags ``h = 1 … ⌊L/2⌋``
    for multiple sequences using batched FFT.

    Parameters
    ----------
    sequences : np.ndarray
        2‑D array of shape ``(n_seq, L)``.
    L : int
        Length of the window.

    Returns
    -------
    np.ndarray
        2‑D array of shape ``(n_seq, L//2)`` containing the normalized
        autocorrelations.
    """
    if sequences.ndim != 2 or sequences.shape[1] != L:
        raise ValueError("Input must be of shape (n_seq, L)")

    # Cast to int64 to avoid overflow.
    seq_int64 = sequences.astype(np.int64)

    # Zero‑pad to length 2*L for linear convolution.
    n = 2 * L
    fft_vals = np.fft.rfft(seq_int64, n=n, axis=1)
    power_spectrum = fft_vals * np.conj(fft_vals)
    autocorr_full = np.fft.irfft(power_spectrum, n=n, axis=1)[:, :L]

    max_lag = L // 2
    lags = np.arange(1, max_lag + 1, dtype=np.int64)
    sums = autocorr_full[:, lags]  # shape (n_seq, max_lag)
    normalisers = (L - lags).astype(np.float64)  # shape (max_lag,)
    return sums.astype(np.float64) / normalisers


# ----------------------------------------------------------------------
# Helper for null_distribution
# ----------------------------------------------------------------------
def _load_mobius_array() -> np.ndarray:
    """
    Load the full Möbius array used throughout the pipeline.

    Returns
    -------
    np.ndarray
        1‑D ``int8`` array containing the Möbius values with a dummy
        zero at index 0.

    Raises
    ------
    FileNotFoundError
        If ``data/raw/mobius_array.npy`` does not exist.
    """
    mobius_path = Path("data/raw/mobius_array.npy")
    if not mobius_path.is_file():
        raise FileNotFoundError(f"Möbius array not found at {mobius_path}")
    return np.load(mobius_path, allow_pickle=False)


# ----------------------------------------------------------------------
# Minimal CLI driver (not used by the tests but kept for completeness)
# ----------------------------------------------------------------------
def main() -> None:
    """
    Simple demonstration that loads a Möbius window, generates a few
    permutations, and prints the shape of the resulting array.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate zero‑preserving permutations for a Möbius window."
    )
    parser.add_argument(
        "--window-start",
        type=int,
        required=True,
        help="1‑based start index of the window in the Möbius array.",
    )
    parser.add_argument(
        "--length",
        type=int,
        required=True,
        help="Length L of the window.",
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=10,
        help="Number of permutations to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20231017,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()

    mobius = _load_mobius_array()
    window = mobius[args.window_start : args.window_start + args.length]
    perms = generate_zero_preserving_permutations(window, args.n_permutations, args.seed)
    print(f"Generated permutations shape: {perms.shape}")


if __name__ == "__main__":
    main()
