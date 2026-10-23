"""
window_index.py

Generate deterministic non‑overlapping window start indices for the
Möbius autocorrelation pipeline.

For each interval length L in {1000, 10000, 100000} we create exactly
100 windows.  Windows are placed on a contiguous tiling with step L,
starting from a random offset drawn from a fixed seed (20231017).
The offset is chosen so that the required number of windows always
fits inside the maximum index N (default 10 000 000).  The resulting
CSV is written to ``data/processed/window_index.csv`` with columns:

    interval_start,interval_length,window_id

where ``interval_start`` is the 1‑based start index (compatible with the
Möbius array that contains a dummy zero at position 0), ``interval_length``
is L, and ``window_id`` runs from 0 to 99 within each L.

The script aborts loudly if the generated windows would overlap or exceed
the maximum index N.  A small unit test is provided in
``tests/unit/test_window_index.py`` to verify the line count (300) and
the non‑overlap property.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List, Tuple

import numpy as np

# ----------------------------------------------------------------------
# Configuration defaults
# ----------------------------------------------------------------------
DEFAULT_N: int = 10_000_000          # Upper bound for the Möbius sieve
DEFAULT_L_VALUES: List[int] = [1000, 10_000, 100_000]
DEFAULT_WINDOWS_PER_L: int = 100
DEFAULT_SEED: int = 20231017
# Use the project's path helper to guarantee the correct directory.
from llmxive_toolkit import paths

DEFAULT_OUTPUT: Path = paths.processed("window_index.csv")

# ----------------------------------------------------------------------


def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of *p* if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)


def _generate_windows_for_length(
    N: int,
    L: int,
    windows_per_L: int,
    rng: np.random.Generator,
) -> List[int]:
    """
    Generate ``windows_per_L`` non‑overlapping start indices for a given
    interval length ``L`` using a tiled layout.

    The tiling is ``offset + k*L`` for k = 0, 1, … .  ``offset`` is a
    deterministic random integer chosen so that the required number of
    windows fits completely inside ``[1, N]`` (the Möbius array is
    1‑based, index 0 is unused).

    Parameters
    ----------
    N : int
        Maximum index (inclusive) of the Möbius array.
    L : int
        Interval length.
    windows_per_L : int
        Number of windows to generate.
    rng : np.random.Generator
        Deterministic random number generator.

    Returns
    -------
    List[int]
        List of start indices (1‑based) of length ``windows_per_L``.
    """
    if L > N:
        raise ValueError(f"Interval length L={L} exceeds N={N}")

    # The largest possible offset that still allows ``windows_per_L``
    # windows is ``max_offset = N - windows_per_L * L``.
    # If this value is negative we cannot fit the required number of
    # windows for the given ``L``.
    max_offset = N - windows_per_L * L
    if max_offset < 0:
        raise RuntimeError(
            f"Not enough room to place {windows_per_L} non‑overlapping windows "
            f"of length {L} within N={N}."
        )

    # Choose a deterministic offset in the allowed range.
    offset = int(rng.integers(0, max_offset + 1))

    # First possible start (1‑based)
    first_start = 1 + offset

    # Generate the required starts; they are guaranteed to fit because
    # ``first_start + (windows_per_L-1)*L + L - 1 <= N``.
    starts = [
        first_start + k * L
        for k in range(windows_per_L)
    ]
    return starts


def generate_window_index(
    N: int = DEFAULT_N,
    L_values: List[int] = DEFAULT_L_VALUES,
    windows_per_L: int = DEFAULT_WINDOWS_PER_L,
    seed: int = DEFAULT_SEED,
    output_path: Path = DEFAULT_OUTPUT,
) -> None:
    """
    Generate the full window index CSV.

    The CSV contains exactly ``len(L_values) * windows_per_L`` rows.
    Each row is unique and windows for a given L never overlap.

    Parameters
    ----------
    N : int
        Upper bound for the Möbius array (inclusive).
    L_values : List[int]
        Interval lengths to process.
    windows_per_L : int
        Number of windows per interval length.
    seed : int
        Seed for the deterministic RNG.
    output_path : Path
        Destination CSV file.
    """
    rng = np.random.default_rng(seed)

    rows: List[Tuple[int, int, int]] = []  # (start, L, window_id)

    for L in L_values:
        starts = _generate_windows_for_length(N, L, windows_per_L, rng)
        for idx, start in enumerate(starts):
            rows.append((start, L, idx))

    # Verify non‑overlap across all rows (strictly for safety)
    # Sort by start for easier checking
    rows_sorted = sorted(rows, key=lambda r: r[0])
    for i in range(1, len(rows_sorted)):
        prev_start, prev_L, _ = rows_sorted[i - 1]
        cur_start, cur_L, _ = rows_sorted[i]
        # windows can only overlap if they belong to the same L,
        # because different L have different step sizes.
        if prev_L == cur_L:
            if cur_start < prev_start + prev_L:
                raise RuntimeError(
                    f"Overlap detected for L={prev_L}: "
                    f"window starting at {prev_start} overlaps with "
                    f"window starting at {cur_start}."
                )

    # Write CSV
    _ensure_parent_dir(output_path)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["interval_start", "interval_length", "window_id"])
        for start, L, wid in rows:
            writer.writerow([start, L, wid])

    print(f"Window index written to {output_path} ({len(rows)} rows)")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic window index for Möbius autocorrelation."
    )
    parser.add_argument(
        "--max",
        type=int,
        default=DEFAULT_N,
        help="Maximum integer N (inclusive) for the Möbius array. Default: %(default)s",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the CSV file. Default: %(default)s",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for offset generation. Default: %(default)s",
    )
    parser.add_argument(
        "--windows-per-L",
        type=int,
        default=DEFAULT_WINDOWS_PER_L,
        help="Number of windows per interval length. Default: %(default)s",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    generate_window_index(
        N=args.max,
        L_values=DEFAULT_L_VALUES,
        windows_per_L=args.windows_per_L,
        seed=args.seed,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
