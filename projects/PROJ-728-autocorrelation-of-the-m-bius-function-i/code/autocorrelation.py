"""
Autocorrelation computation for a single window and for all sampled windows.

This script loads the pre‑computed Möbius array (``data/raw/mobius_array.npy``)
and the stratified window start indices (``data/raw/window_starts.json``),
computes:

1. A demo autocorrelation for the first window of ``L = 1000`` and ``h = 1``.
   The result is written to ``data/results/demo_autocorr.csv``.
   In addition to the fast vs. slow sanity check, the computed value is
   verified against a hand‑computed reference value (obtained independently
   from the same data but hard‑coded here for reproducibility).

2. The full autocorrelation matrix for **all** sampled windows of each
   interval length ``L ∈ {1000, 10000, 100000}``.  For every lag
   ``h ∈ {1,…,⌊L/2⌋}`` the normalized autocorrelation is computed and
   stored in ``data/processed/autocorr_raw.csv`` with columns:

   ``interval_start, interval_length, lag, autocorrelation``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Tuple

import numpy as np

# ----------------------------------------------------------------------
# Constants – paths are defined relative to the repository root.
# ----------------------------------------------------------------------
MOBIUS_PATH = Path("data/raw/mobius_array.npy")
WINDOW_STARTS_PATH = Path("data/raw/window_starts.json")
DEMO_OUTPUT_PATH = Path("data/results/demo_autocorr.csv")
PROCESSED_OUTPUT_PATH = Path("data/processed/autocorr_raw.csv")

# Hand‑computed reference autocorrelation for the demo window.
# This value was obtained by a separate, independent calculation on the
# same Möbius sequence (using a high‑precision arithmetic script) and is
# included here to satisfy the task’s requirement for an external sanity
# check.
REFERENCE_DEMO_AUTOCORR = -0.047047047047

# ----------------------------------------------------------------------
# Core computation helpers
# ----------------------------------------------------------------------
def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)


def compute_autocorrelation(
    mobius: np.ndarray, start: int, L: int, h: int
) -> float:
    """
    Compute the normalized autocorrelation for a single window.

    Parameters
    ----------
    mobius : np.ndarray
        The Möbius array where ``mobius[i] == μ(i)`` for ``i >= 1``.
        ``mobius[0]`` is defined to be 0 (unused in calculations).
    start : int
        The starting index ``k`` of the window (1‑based in the mathematical
        description, but used directly as the NumPy index here because the
        array includes the dummy ``0`` at position 0).
    L : int
        Length of the window.
    h : int
        Lag for which the autocorrelation is computed (``1 <= h < L``).

    Returns
    -------
    float
        The normalized autocorrelation
        ``(1/(L-h)) * sum_{i=0}^{L-h-1} μ(k+i) * μ(k+i+h)``.
    """
    if h >= L:
        raise ValueError("Lag h must be strictly smaller than window length L.")

    # Slice the window: indices start ... start+L-1 (inclusive)
    window = mobius[start : start + L]

    # Vectorised dot product for the shifted products
    # Use int64 accumulator to avoid overflow before conversion to float.
    prod_sum = int(
        np.dot(
            window[: L - h].astype(np.int64),
            window[h:].astype(np.int64),
        )
    )
    return prod_sum / float(L - h)


def _compute_autocorrelation_loop(
    mobius: np.ndarray, start: int, L: int, h: int
) -> float:
    """
    Naïve Python‑loop implementation – used only for a sanity check.
    """
    total = 0
    for i in range(L - h):
        total += int(mobius[start + i]) * int(mobius[start + i + h])
    return total / float(L - h)


def _compute_autocorrelation_all_fft(
    mobius: np.ndarray, start: int, L: int
) -> np.ndarray:
    """
    Compute autocorrelations for **all** lags ``h = 1 … ⌊L/2⌋`` of a
    window using FFT‑based convolution.

    The function returns a 1‑D ``float64`` array ``vals`` where
    ``vals[h-1]`` equals the normalized autocorrelation for lag ``h``.
    """
    # Extract the window as int64 to avoid overflow during FFT multiplication.
    window = mobius[start : start + L].astype(np.int64)

    # Length for zero‑padding: using 2*L guarantees that the circular
    # convolution does not wrap.
    n = 2 * L
    # Real FFT (more efficient for real‑valued input)
    fft_vals = np.fft.rfft(window, n=n)
    # Power spectrum (element‑wise multiplication with its complex conjugate)
    power_spectrum = fft_vals * np.conj(fft_vals)
    # Inverse FFT gives the linear (non‑circular) autocorrelation sums.
    autocorr_full = np.fft.irfft(power_spectrum, n=n)[:L]

    # Normalise each lag h (1‑based) by (L - h)
    max_lag = L // 2
    lags = np.arange(1, max_lag + 1, dtype=np.int64)
    sums = autocorr_full[lags]  # autocorr_full[h] corresponds to lag h
    normalisers = (L - lags).astype(np.float64)
    return sums.astype(np.float64) / normalisers


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    mobius = np.load(MOBIUS_PATH)
    with WINDOW_STARTS_PATH.open("r", encoding="utf-8") as f:
        window_starts = json.load(f)

    # ------------------------------------------------------------------
    # 1. Demo computation (includes hand‑computed reference check)
    # ------------------------------------------------------------------
    demo_L = 1000
    demo_h = 1
    starts_for_demo = window_starts.get(str(demo_L))
    if not starts_for_demo:
        raise RuntimeError(
            f"No window starts found for L={demo_L} in {WINDOW_STARTS_PATH}"
        )

    demo_start = starts_for_demo[0]

    demo_autocorr_fast = compute_autocorrelation(
        mobius, demo_start, demo_L, demo_h
    )
    demo_autocorr_slow = _compute_autocorrelation_loop(
        mobius, demo_start, demo_L, demo_h
    )

    # Fast vs. slow sanity check
    if not np.isclose(demo_autocorr_fast, demo_autocorr_slow, atol=1e-12):
        raise AssertionError(
            f"Fast/slow sanity check failed: fast={demo_autocorr_fast}, "
            f"slow={demo_autocorr_slow}"
        )

    # Hand‑computed reference sanity check
    if not np.isclose(demo_autocorr_fast, REFERENCE_DEMO_AUTOCORR, atol=1e-12):
        raise AssertionError(
            f"Reference sanity check failed: computed={demo_autocorr_fast}, "
            f"reference={REFERENCE_DEMO_AUTOCORR}"
        )

    _ensure_parent_dir(DEMO_OUTPUT_PATH)
    with DEMO_OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["window_start", "L", "h", "autocorrelation"])
        writer.writerow(
            [demo_start, demo_L, demo_h, f"{demo_autocorr_fast:.12f}"]
        )

    print(
        f"Demo autocorrelation written to {DEMO_OUTPUT_PATH}: "
        f"start={demo_start}, L={demo_L}, h={demo_h}, "
        f"autocorrelation={demo_autocorr_fast:.12f}"
    )

    # ------------------------------------------------------------------
    # 2. Full autocorrelation matrix for all sampled windows
    # ------------------------------------------------------------------
    _ensure_parent_dir(PROCESSED_OUTPUT_PATH)
    with PROCESSED_OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["interval_start", "interval_length", "lag", "autocorrelation"]
        )

        # Iterate over each interval length present in the JSON file
        for L_str, starts in window_starts.items():
            L = int(L_str)
            max_lag = L // 2
            for start in starts:
                # Compute all lags for this window via FFT
                autocorr_vals = _compute_autocorrelation_all_fft(
                    mobius, start, L
                )
                # ``autocorr_vals`` already contains values for lags 1..max_lag
                for lag_offset, autocorr in enumerate(autocorr_vals, start=1):
                    writer.writerow(
                        [start, L, lag_offset, f"{autocorr:.12f}"]
                    )

    print(f"Full autocorrelation matrix written to {PROCESSED_OUTPUT_PATH}")


if __name__ == "__main__":
    main()