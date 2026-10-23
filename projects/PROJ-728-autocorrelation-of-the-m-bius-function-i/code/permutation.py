"""
permutation.py
---------------
Implements the permutation engine to generate a null distribution for the
Möbius autocorrelation. For each window, it preserves the zero positions
and uniformly shuffles the signs of non-zero entries to test the
"random sign heuristic".

The script computes two-sided p-values and 95% confidence intervals for
all lags h = 1...floor(L/2) using batched FFTs.
"""

from __future__ import annotations

import argparse
import csv
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List

__all__ = [
    "generate_zero_preserving_permutations",
    "generate_permutations",   # Compatibility alias for legacy imports
    "compute_batched_autocorrelations",
    "main",
]

def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of p if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)

def generate_zero_preserving_permutations(
    window: np.ndarray, n_permutations: int, seed: int
) -> np.ndarray:
    """
    Generate n_permutations that keep zero positions fixed and uniformly
    shuffle the signs of the non-zero entries.
    """
    # Boolean mask of zero positions
    zero_mask = (window == 0)
    # Extract the mutable sign entries (+1, -1)
    signs = window[~zero_mask]
    
    rng = np.random.default_rng(seed)
    perms = np.empty((n_permutations, len(window)), dtype=window.dtype)

    for i in range(n_permutations):
        shuffled_signs = rng.permutation(signs)
        new_win = np.empty_like(window)
        new_win[zero_mask] = 0
        new_win[~zero_mask] = shuffled_signs
        perms[i] = new_win

    return perms

# ----------------------------------------------------------------------
# Compatibility layer
# ----------------------------------------------------------------------
def generate_permutations(
    window: np.ndarray, n_permutations: int, seed: int
) -> np.ndarray:
    """
    Legacy wrapper retained for backward‑compatibility.

    Earlier versions of the pipeline imported a function named
    ``generate_permutations`` from this module.  The implementation was
    later renamed to :func:`generate_zero_preserving_permutations` to
    better reflect its behaviour.  The null‑distribution module still
    expects the old name, so we provide this thin wrapper that forwards
    the call.
    """
    return generate_zero_preserving_permutations(window, n_permutations, seed)

def compute_batched_autocorrelations(sequences: np.ndarray, L: int) -> np.ndarray:
    """
    Compute normalized autocorrelations for all lags h = 1...floor(L/2)
    for multiple sequences using batched FFT.
    
    Parameters:
        sequences: 2D array of shape (n_seq, L)
        L: Length of the window
    Returns:
        2D array of shape (n_seq, L//2)
    """
    n_seq = sequences.shape[0]
    # Padding to 2L to avoid circular correlation
    n_fft = 2 * L
    
    # Real FFT across the last axis
    fft_vals = np.fft.rfft(sequences, n=n_fft, axis=-1)
    # Power spectrum
    power_spectrum = fft_vals * np.conj(fft_vals)
    # Inverse FFT to get linear autocorrelation sums
    autocorr_full = np.fft.irfft(power_spectrum, n=n_fft, axis=-1)

    # Normalise each lag h = 1 .. L//2
    max_lag = L // 2
    lags = np.arange(1, max_lag + 1, dtype=np.int64)
    # Extract the sums for the required lags
    sums = autocorr_full[:, lags]
    # Normalization factor (L - h)
    normalisers = (L - lags).astype(np.float64)
    
    return sums.astype(np.float64) / normalisers

def _compute_single_window_obs(mobius: np.ndarray, start: int, L: int) -> np.ndarray:
    """Compute observed autocorrelations for all lags h = 1...L//2."""
    # Use the same FFT logic as the batched version but for one sequence
    window = mobius[start : start + L]
    # Reshape to (1, L) to reuse compute_batched_autocorrelations
    res = compute_batched_autocorrelations(window[np.newaxis, :], L)
    return res[0]

def main() -> None:
    """
    Pipeline entry point for T007: Permutation engine & null distribution.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", type=Path, required=True, help="Output stats CSV")
    parser.add_argument("--array", type=Path, required=True, help="Möbius array npy")
    args = parser.parse_args()

    # Load data
    if not args.array.is_file():
        raise FileNotFoundError(f"Möbius array not found: {args.array}")
    mobius = np.load(args.array)

    window_index_path = Path("data/processed/window_index.csv")
    if not window_index_path.is_file():
        raise FileNotFoundError(f"Window index not found: {window_index_path}")
    
    windows_df = pd.read_csv(window_index_path)

    # Setup CSV output
    header = [
        "interval_start", "interval_length", "lag", "autocorrelation",
        "p_value", "adjusted_p_value", "ci_lower", "ci_upper",
        "zero_count", "sensitivity_flag", "theoretical_variance"
    ]
    _ensure_parent_dir(args.stats)
    
    # Constants
    N_PERMS = 1000
    BASE_SEED = 20231017
    SIGMA2 = (6.0 / np.pi**2) * (1.0 - 6.0 / np.pi**2)

    with args.stats.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for _, row in windows_df.iterrows():
            start = int(row["interval_start"])
            L = int(row["interval_length"])
            window_id = int(row["window_id"])
            
            window = mobius[start : start + L]
            zero_count = int(np.count_nonzero(window == 0))

            if zero_count == L:
                # All zeros: undefined autocorrelation
                max_lag = L // 2
                for lag in range(1, max_lag + 1):
                    writer.writerow([
                        start, L, lag, np.nan, np.nan, np.nan, 
                        np.nan, np.nan, zero_count, "not_applicable", SIGMA2 / L
                    ])
                continue

            # 1. Observed values
            obs_vals = _compute_single_window_obs(mobius, start, L)

            # 2. Null distribution
            seed = BASE_SEED + window_id
            perms = generate_zero_preserving_permutations(window, N_PERMS, seed)
            null_matrix = compute_batched_autocorrelations(perms, L)

            # 3. Process each lag
            max_lag = L // 2
            for lag_idx in range(max_lag):
                lag = lag_idx + 1
                obs = obs_vals[lag_idx]
                null_vals = null_matrix[:, lag_idx]

                # Two-sided p-value: (#{|r_perm| >= |r_obs|} + 1) / 1001
                count_extreme = np.sum(np.abs(null_vals) >= np.abs(obs))
                p_val = (count_extreme + 1) / (N_PERMS + 1)

                # Clamp p-values
                p_val = max(0.001, min(0.999, p_val))

                # Confidence Bounds
                ci_lower = np.percentile(null_vals, 2.5)
                ci_upper = np.percentile(null_vals, 97.5)

                writer.writerow([
                    start, L, lag, float(obs), float(p_val), np.nan,
                    float(ci_lower), float(ci_upper), zero_count, "stable", SIGMA2 / L
                ])

    print(f"Successfully wrote permutation stats to {args.stats}")

if __name__ == "__main__":
    main()