"""
Null distribution computation for Möbius autocorrelation.

For every sampled window (defined in ``data/raw/window_starts.json``) and
for every lag ``h`` in ``1 .. floor(L/2)`` this script:

1. Loads the Möbius array (``data/raw/mobius_array.npy``).
2. Computes the observed autocorrelation for all lags in the window.
3. Generates ``n_permutations`` block‑permuted versions of the window
   (using :func:`permutation.generate_permutations`).
4. Computes autocorrelations for each permuted sequence.
5. Derives a two‑sided p‑value and a 95 % confidence interval from the
   permutation null distribution.
6. Writes a CSV file ``data/processed/autocorr_stats.csv`` with columns::

   interval_start, interval_length, lag, autocorrelation,
   p_value, ci_lower, ci_upper, zero_count

The script is deliberately self‑contained and can be executed directly:

    python -m code.null_distribution

It respects the deterministic seed used throughout the project (default
seed=42) to ensure reproducibility.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

# Import helpers from sibling modules (public API surface)
from autocorrelation import _compute_autocorrelation_all_fft, compute_autocorrelation
from permutation import (
    generate_permutations,
    _load_mobius_array,
    _load_window_starts,
)

# ----------------------------------------------------------------------
# Configuration constants (mirroring defaults used elsewhere)
# ----------------------------------------------------------------------
MOBIUS_PATH = Path("data/raw/mobius_array.npy")
WINDOW_STARTS_PATH = Path("data/raw/window_starts.json")
OUTPUT_CSV = Path("data/processed/autocorr_stats.csv")

# Number of permutations per window – matches the default in
# ``permutation.generate_permutations``.
N_PERMUTATIONS = 1000
BLOCK_SIZE = 100
RNG_SEED = 42  # deterministic seed for reproducibility

def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)

def _two_sided_p_value(obs: float, null_vals: np.ndarray) -> float:
    """
    Compute a two‑sided p‑value for ``obs`` against the permutation null.

    The p‑value is the proportion of null values whose absolute magnitude
    is greater than or equal to ``abs(obs)``.  If ``obs`` is NaN the
    function returns NaN.
    """
    if np.isnan(obs):
        return float("nan")
    greater_eq = np.abs(null_vals) >= np.abs(obs)
    return greater_eq.mean()

def _confidence_interval(
    null_vals: np.ndarray, lower: float = 2.5, upper: float = 97.5
) -> tuple[float, float]:
    """
    Return the lower and upper percentiles of ``null_vals``.
    """
    if null_vals.size == 0:
        return (float("nan"), float("nan"))
    # ``np.percentile`` switched from the ``interpolation`` keyword to
    # ``method`` in NumPy 1.22+. Using ``method='linear'`` works on all
    # supported versions.
    lo = np.percentile(null_vals, lower, method="linear")
    hi = np.percentile(null_vals, upper, method="linear")
    return (float(lo), float(hi))

def process_window(
    mobius: np.ndarray,
    start: int,
    L: int,
    *,
    n_permutations: int = N_PERMUTATIONS,
    block_size: int = BLOCK_SIZE,
    seed: int | None = RNG_SEED,
) -> List[dict]:
    """
    Process a single window and return a list of result rows (one per lag).

    Parameters
    ----------
    mobius : np.ndarray
        Full Möbius array (index 0 unused).
    start : int
        1‑based start index of the window.
    L : int
        Length of the window.
    n_permutations, block_size, seed : int
        Passed through to :func:`permutation.generate_permutations`.

    Returns
    -------
    List[dict]
        Each dict corresponds to a CSV row with the required columns.
    """
    # Extract the window slice (inclusive of start, exclusive of start+L)
    window = mobius[start : start + L]

    zero_count = int(np.count_nonzero(window == 0))

    # Edge‑case: window consists entirely of zeros → autocorrelation undefined.
    if zero_count == L:
        # Record NaNs for statistical fields.
        return [
            {
                "interval_start": start,
                "interval_length": L,
                "lag": h,
                "autocorrelation": float("nan"),
                "p_value": float("nan"),
                "ci_lower": float("nan"),
                "ci_upper": float("nan"),
                "zero_count": zero_count,
            }
            for h in range(1, L // 2 + 1)
        ]

    # Observed autocorrelations for all lags using the FFT‑based routine.
    observed = _compute_autocorrelation_all_fft(mobius, start, L)  # shape (floor(L/2),)

    # Generate permutations.
    perms = generate_permutations(
        mobius,
        start,
        L,
        block_size=block_size,
        n_permutations=n_permutations,
        seed=seed,
    )  # shape (n_permutations, L)

    # Compute autocorrelations for each permuted sequence.
    # We reuse the FFT routine for each permutation; this is vectorised
    # over the first axis by looping (still fast enough for the given sizes).
    perm_ac_vals = np.empty((n_permutations, observed.shape[0]), dtype=np.float64)
    for idx, perm in enumerate(perms):
        # ``perm`` is a 1‑D array of length L.
        # To reuse the existing FFT helper we temporarily place it into a
        # dummy full Möbius array where the window starts at index 0.
        # This avoids re‑implementing the FFT logic.
        dummy_full = np.concatenate(([0], perm))  # prepend dummy 0 to match API
        perm_ac_vals[idx] = _compute_autocorrelation_all_fft(dummy_full, 1, L)

    # Assemble rows.
    rows = []
    for lag_idx, obs_val in enumerate(observed, start=1):
        null_vals = perm_ac_vals[:, lag_idx - 1]
        p_val = _two_sided_p_value(obs_val, null_vals)
        ci_lo, ci_hi = _confidence_interval(null_vals)
        rows.append(
            {
                "interval_start": start,
                "interval_length": L,
                "lag": lag_idx,
                "autocorrelation": float(obs_val),
                "p_value": float(p_val),
                "ci_lower": float(ci_lo),
                "ci_upper": float(ci_hi),
                "zero_count": zero_count,
            }
        )
    return rows

def main() -> None:
    """
    Entry‑point for the null‑distribution computation.

    The function iterates over all windows defined in
    ``data/raw/window_starts.json`` and writes the aggregated results to
    ``data/processed/autocorr_stats.csv``.
    """
    mobius = _load_mobius_array(MOBIUS_PATH)
    window_map = _load_window_starts(WINDOW_STARTS_PATH)

    all_rows: List[dict] = []

    for L_str, starts in window_map.items():
        L = int(L_str)
        for start in starts:
            rows = process_window(
                mobius,
                start,
                L,
                n_permutations=N_PERMUTATIONS,
                block_size=BLOCK_SIZE,
                seed=RNG_SEED,
            )
            all_rows.extend(rows)

    # Convert to DataFrame for convenient CSV output.
    df = pd.DataFrame(all_rows)
    # Ensure the column order matches the specification.
    df = df[
        [
            "interval_start",
            "interval_length",
            "lag",
            "autocorrelation",
            "p_value",
            "ci_lower",
            "ci_upper",
            "zero_count",
        ]
    ]

    _ensure_parent_dir(OUTPUT_CSV)
    df.to_csv(OUTPUT_CSV, index=False, float_format="%.12g")
    print(f"Null‑distribution statistics written to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()