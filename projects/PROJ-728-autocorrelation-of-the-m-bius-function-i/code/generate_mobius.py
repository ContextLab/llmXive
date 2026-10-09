"""
generate_mobius.py

This script generates the Möbius function array for n = 1 .. N using the
linear sieve implementation in ``code.sieve`` and stores the result as a
NumPy ``.npy`` file.  It then selects M = 20 stratified random window start
indices for each interval length L ∈ {10³, 10⁴, 10⁵} using a fixed random
seed (42) and writes the indices to ``data/raw/window_starts.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

# Import the public API from the existing sieve module.
from sieve import save_mobius_array

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
N: int = 10_000_000               # Upper bound for the Möbius sieve.
M: int = 20                       # Number of stratified windows per L.
L_VALUES: list[int] = [10**3, 10**4, 10**5]  # Interval lengths.
SEED: int = 42                    # Fixed seed for reproducibility.
MOBIUS_PATH: Path = Path("data/raw/mobius_array.npy")
STARTS_PATH: Path = Path("data/raw/window_starts.json")

def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)

def generate_mobius_and_windows() -> None:
    """
    Generate the Möbius array and the stratified window start indices.

    The function performs three steps:
    1. Compute and save the Möbius array to ``MOBIUS_PATH``.
    2. For each ``L`` in ``L_VALUES`` choose ``M`` start positions
       via stratified random sampling.
    3. Write the mapping ``{L: [starts...]}`` to ``STARTS_PATH`` in JSON
       format.  Keys are strings so that JSON round‑trips without loss.
    """
    # ------------------------------------------------------------------
    # Step 1 – generate the Möbius array.
    # ------------------------------------------------------------------
    _ensure_parent_dir(MOBIUS_PATH)
    # ``save_mobius_array`` both computes and writes the array.
    save_mobius_array(N, MOBIUS_PATH)

    # ------------------------------------------------------------------
    # Step 2 – stratified random sampling of window starts.
    # ------------------------------------------------------------------
    rng = np.random.default_rng(SEED)

    starts_by_L: dict[str, list[int]] = {}
    for L in L_VALUES:
        max_start = N - L + 1          # inclusive upper bound for a start.
        # Size of each stratum (except possibly the last one).
        stride = max_start // M
        starts: list[int] = []

        for i in range(M):
            # Define the bounds of the i‑th stratum.
            lower = i * stride + 1
            # The last stratum gets any remainder.
            upper = (i + 1) * stride if i < M - 1 else max_start
            # Draw a uniformly random integer in [lower, upper].
            start = int(rng.integers(lower, upper + 1))
            starts.append(start)

        starts_by_L[str(L)] = starts

    # ------------------------------------------------------------------
    # Step 3 – write the JSON file.
    # ------------------------------------------------------------------
    _ensure_parent_dir(STARTS_PATH)
    with STARTS_PATH.open("w", encoding="utf-8") as fp:
        json.dump(starts_by_L, fp, indent=2, sort_keys=True)

def main() -> None:
    """Entry‑point for ``python -m code.generate_mobius``."""
    generate_mobius_and_windows()
    print(f"Möbius array written to: {MOBIUS_PATH}")
    print(f"Window start indices written to: {STARTS_PATH}")

if __name__ == "__main__":
    main()
