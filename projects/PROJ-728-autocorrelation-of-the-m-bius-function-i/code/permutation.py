"""permutation.py
----------------
Utilities for generating zero‑preserving sign permutations of Möbius
windows and computing batched autocorrelations.  The original module
already provides the core functionality required by the pipeline.

This revision adds a small helper that the ``null_distribution`` module
expects: ``_load_window_starts``.  It simply reads the JSON file
``data/raw/window_starts.json`` (produced by ``generate_mobius.py``) and
returns a mapping from interval length ``L`` to a list of start indices.

Adding this function resolves the import error that prevented the
orchestrator from loading the module, allowing the pipeline (and the
unit tests) to run successfully.
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
    "_load_window_starts",  # newly added
]

# ----------------------------------------------------------------------
# Existing public API (unchanged)
# ----------------------------------------------------------------------

def generate_zero_preserving_permutations(
    window: np.ndarray, n_permutations: int, seed: int
) -> np.ndarray:
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
    nz_mask = window != 0
    nz_values = window[nz_mask]
    L = window.shape[0]

    perms = np.empty((n_permutations, L), dtype=window.dtype)
    # Zero positions are copied directly.
    perms[:, ~nz_mask] = 0

    for i in range(n_permutations):
        shuffled = rng.permutation(nz_values)
        perms[i, nz_mask] = shuffled
    return perms


# Legacy wrapper retained for backward compatibility.
def generate_permutations(window: np.ndarray, n_permutations: int, seed: int) -> np.ndarray:
    """Legacy alias for :func:`generate_zero_preserving_permutations`."""
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
    # Convert to int64 to avoid overflow during FFT multiplication.
    windows = sequences.astype(np.int64)
    n = 2 * L
    fft_vals = np.fft.rfft(windows, n=n, axis=1)
    power_spectrum = fft_vals * np.conj(fft_vals)
    autocorr_full = np.fft.irfft(power_spectrum, n=n, axis=1)[:, :L]

    max_lag = L // 2
    lags = np.arange(1, max_lag + 1, dtype=np.int64)
    sums = autocorr_full[:, lags]  # shape (n_seq, max_lag)
    normalisers = (L - lags).astype(np.float64)
    return sums.astype(np.float64) / normalisers


# ----------------------------------------------------------------------
# Helper required by ``null_distribution`` (newly added)
# ----------------------------------------------------------------------

def _load_window_starts() -> Dict[int, List[int]]:
    """
    Load the JSON mapping ``{L: [start, …]}`` produced by
    ``generate_mobius.py`` (or ``code.generate_mobius``).  The JSON file
    lives at ``data/raw/window_starts.json`` and uses string keys; this
    helper converts them to integers for convenient downstream use.

    Returns
    -------
    dict[int, list[int]]
        Mapping from interval length ``L`` to a list of start indices.
    """
    path = Path("data/raw/window_starts.json")
    if not path.is_file():
        raise FileNotFoundError(f"Window starts file not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


# ----------------------------------------------------------------------
# CLI entry point (unchanged)
# ----------------------------------------------------------------------

def main() -> None:
    """
    Minimal command‑line driver that demonstrates the permutation engine.
    It is not used by the unit tests but provides a convenient manual
    sanity check.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Möbius permutation utilities")
    parser.add_argument(
        "--window", type=str, required=True, help="Path to a NumPy .npy file containing a Möbius window"
    )
    parser.add_argument(
        "--permutations",
        type=int,
        default=10,
        help="Number of zero‑preserving permutations to generate",
    )
    parser.add_argument("--seed", type=int, default=20231017, help="RNG seed")
    args = parser.parse_args()

    window = np.load(args.window, allow_pickle=False)
    perms = generate_zero_preserving_permutations(window, args.permutations, args.seed)
    autocorrs = compute_batched_autocorrelations(perms, len(window))
    print("First permutation autocorrelations (first 5 lags):", autocorrs[0, :5])


if __name__ == "__main__":
    main()