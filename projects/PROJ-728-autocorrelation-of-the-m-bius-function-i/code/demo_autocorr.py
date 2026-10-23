"""
demo_autocorr.py
----------------
Compute the normalized autocorrelation for the first window (L=1000, h=1)
and write the result to `data/processed/demo_autocorr.csv`. This script
is used by task T005 and also by the demo mode of the pipeline.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

# Paths to required data files
MOBIUS_PATH = Path("data/raw/mobius_array.npy")
# The window starts are stored by `generate_mobius.py` in the raw folder.
WINDOW_STARTS_JSON = Path("data/raw/window_starts.json")
# Output path required by task T005
OUTPUT_CSV = Path("data/processed/demo_autocorr.csv")

# Hand‑computed reference autocorrelation for the demo window.
REFERENCE_AUTOCORR = -0.047047047047

def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)

def load_mobius_array() -> np.ndarray:
    """Load the Möbius array; raise if the file does not exist."""
    if not MOBIUS_PATH.is_file():
        raise FileNotFoundError(f"Möbius array not found at {MOBIUS_PATH}")
    return np.load(MOBIUS_PATH, allow_pickle=False)

def load_window_starts() -> dict[int, list[int]]:
    """Load the JSON mapping ``{L: [start, …]}``."""
    import json

    if not WINDOW_STARTS_JSON.is_file():
        raise FileNotFoundError(f"Window starts file not found at {WINDOW_STARTS_JSON}")
    with WINDOW_STARTS_JSON.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    # Keys are strings in the JSON; convert to ints for convenience.
    return {int(k): v for k, v in raw.items()}

def compute_autocorrelation(mobius: np.ndarray, start: int, L: int, h: int) -> float:
    """
    Compute the normalized autocorrelation for a single window.

    Parameters
    ----------
    mobius : np.ndarray
        Möbius array (int8) with a dummy zero at index 0.
    start : int
        1‑based start index of the window.
    L : int
        Length of the window.
    h : int
        Lag (1 ≤ h < L).

    Returns
    -------
    float
        Normalized autocorrelation ``(1/(L‑h)) * Σ μ(k+i) μ(k+i+h)``.
    """
    if h >= L:
        raise ValueError("Lag h must be strictly smaller than window length L.")
    window = mobius[start : start + L]
    prod_sum = int(
        np.dot(
            window[: L - h].astype(np.int64),
            window[h:].astype(np.int64),
        )
    )
    return prod_sum / float(L - h)

def main() -> None:
    """
    Execute the demo autocorrelation computation and write the CSV.
    The CSV contains exactly one row with columns:
    interval_start,interval_length,lag,autocorrelation
    """
    mobius = load_mobius_array()
    window_map = load_window_starts()

    demo_L = 1000
    demo_h = 1
    starts = window_map.get(demo_L)
    if not starts:
        raise RuntimeError(f"No window start found for L={demo_L}")

    demo_start = starts[0]

    # Compute autocorrelation using the fast implementation.
    autocorr_val = compute_autocorrelation(mobius, demo_start, demo_L, demo_h)

    # Verify against the hand‑computed reference (absolute tolerance 1e‑9).
    if not np.isclose(autocorr_val, REFERENCE_AUTOCORR, atol=1e-9):
        raise AssertionError(
            f"Demo autocorrelation {autocorr_val:.12f} does not match reference "
            f"{REFERENCE_AUTOCORR:.12f}"
        )

    # Write the result to the required CSV location.
    _ensure_parent_dir(OUTPUT_CSV)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["interval_start", "interval_length", "lag", "autocorrelation"])
        writer.writerow([demo_start, demo_L, demo_h, f"{autocorr_val:.12f}"])

    print(f"Demo autocorrelation written to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
