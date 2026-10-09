"""
permutation.py
---------------
Implements block‑permutation generation for a window of the Möbius sequence.

The permutation scheme respects the **global zero‑density**: each permuted
sequence contains exactly the same multiset of values (‑1, 0, +1) as the
original window.  This is achieved by dividing the window into contiguous
blocks of a fixed size `b` (default 100) and shuffling the order of the
blocks while keeping the internal order of each block unchanged.

The module provides a single public helper:

* ``generate_permutations`` – given the full Möbius array, a window start
  index, and a window length, returns a NumPy array of shape
  ``(n_permutations, L)`` containing the permuted windows.

A small CLI is also provided for ad‑hoc testing; it reads the Möbius
array from ``data/raw/mobius_array.npy`` and the window‑start mapping from
``data/raw/window_starts.json`` and writes the permutations for a single
window to ``data/processed/permutations_{L}_{start}.npy``.

The implementation is pure NumPy and deterministic when a ``seed`` is
supplied (default 42).  It raises clear errors if the requested window
exceeds the bounds of the Möbius array.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import numpy as np

__all__ = [
    "generate_permutations",
    "main",
]


def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)


def _validate_window(mobius: np.ndarray, start: int, L: int) -> None:
    """Validate that ``start`` and ``L`` describe a legal window."""
    if start < 1:
        raise ValueError("Window start must be >= 1 (1‑based indexing).")
    if L <= 0:
        raise ValueError("Window length L must be positive.")
    if start + L - 1 >= mobius.shape[0]:
        raise ValueError(
            f"Window [{start}, {start+L-1}] exceeds Möbius array length "
            f"{mobius.shape[0]-1}."
        )


def _split_into_blocks(window: np.ndarray, block_size: int) -> list[np.ndarray]:
    """
    Split ``window`` into contiguous blocks of size ``block_size``.

    The final block may be shorter if ``len(window)`` is not a multiple of
    ``block_size``.
    """
    if block_size <= 0:
        raise ValueError("block_size must be a positive integer.")
    n = len(window)
    blocks = [
        window[i : min(i + block_size, n)] for i in range(0, n, block_size)
    ]
    return blocks


def generate_permutations(
    mobius: np.ndarray,
    start: int,
    L: int,
    *,
    block_size: int = 100,
    n_permutations: int = 1000,
    seed: Optional[int] = 42,
) -> np.ndarray:
    """
    Generate ``n_permutations`` block‑permuted sequences for a given window.

    Parameters
    ----------
    mobius : np.ndarray
        The full Möbius array (``mobius[0]`` is a dummy 0, values start at
        index 1).
    start : int
        1‑based start index of the window within ``mobius``.
    L : int
        Length of the window.
    block_size : int, default 100
        Size of each block that will be shuffled.  The last block may be
        smaller.
    n_permutations : int, default 1000
        Number of distinct permutations to generate.
    seed : int | None, default 42
        Seed for the random number generator.  If ``None`` the RNG is not
        seeded, yielding nondeterministic output.

    Returns
    -------
    np.ndarray
        Array of shape ``(n_permutations, L)`` where each row is a
        permuted version of the original window.  The multiset of values
        (‑1, 0, +1) is identical to the original window, guaranteeing
        preservation of the global zero‑density.
    """
    _validate_window(mobius, start, L)

    # Extract the window (NumPy uses 0‑based indexing)
    window = mobius[start : start + L]

    # Split into blocks
    blocks = _split_into_blocks(window, block_size)
    n_blocks = len(blocks)

    # Prepare RNG
    rng = np.random.default_rng(seed)

    # Pre‑allocate result array
    perms = np.empty((n_permutations, L), dtype=window.dtype)

    for i in range(n_permutations):
        # Random permutation of block indices
        permuted_indices = rng.permutation(n_blocks)
        # Concatenate the blocks in the new order
        permuted_window = np.concatenate([blocks[idx] for idx in permuted_indices])
        # In the unlikely case the concatenated length differs from L (should
        # not happen), truncate or pad with zeros to match L.
        if permuted_window.shape[0] != L:
            permuted_window = permuted_window[:L]
        perms[i] = permuted_window

    return perms


def _load_mobius_array(path: Path = Path("data/raw/mobius_array.npy")) -> np.ndarray:
    """Load the Möbius array from disk; raise if the file does not exist."""
    if not path.is_file():
        raise FileNotFoundError(f"Möbius array not found at {path}")
    return np.load(path, allow_pickle=False)


def _load_window_starts(
    path: Path = Path("data/raw/window_starts.json"),
) -> dict[int, list[int]]:
    """
    Load the JSON mapping ``{L: [start, ...]}`` and convert keys to ``int``.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Window starts file not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    # Convert keys from strings to ints for easier handling
    return {int(k): v for k, v in raw.items()}


def main() -> None:
    """
    CLI entry point.

    Example usage:
    ```bash
    python -m code.permutation --L 1000 --start 44622 --output data/processed/permutations_1000_44622.npy
    ```

    If ``--run`` is supplied, the script iterates over **all** windows
    defined in ``data/raw/window_starts.json`` and writes a separate ``.npy``
    file for each combination of ``L`` and ``start``.
    """
    parser = argparse.ArgumentParser(
        description="Generate block‑permuted Möbius windows."
    )
    parser.add_argument(
        "--L",
        type=int,
        help="Length of the window (required unless --run is used).",
    )
    parser.add_argument(
        "--start",
        type=int,
        help="1‑based start index of the window (required unless --run is used).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write the permutations array (n_permutations, L).",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=100,
        help="Size of blocks to shuffle (default: 100).",
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=1000,
        help="Number of permutations to generate (default: 1000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Generate permutations for every window in window_starts.json.",
    )
    args = parser.parse_args()

    mobius = _load_mobius_array()

    if args.run:
        window_map = _load_window_starts()
        for L, starts in window_map.items():
            for start in starts:
                perms = generate_permutations(
                    mobius,
                    start,
                    L,
                    block_size=args.block_size,
                    n_permutations=args.n_permutations,
                    seed=args.seed,
                )
                out_path = Path("data/processed") / f"permutations_{L}_{start}.npy"
                _ensure_parent_dir(out_path)
                np.save(out_path, perms)
                print(f"Saved {perms.shape[0]} permutations for L={L}, start={start} → {out_path}")
    else:
        if args.L is None or args.start is None:
            parser.error("When not using --run, both --L and --start must be provided.")
        perms = generate_permutations(
            mobius,
            args.start,
            args.L,
            block_size=args.block_size,
            n_permutations=args.n_permutations,
            seed=args.seed,
        )
        if args.output is None:
            # Default output location mirrors the pattern used in --run mode
            out_path = Path("data/processed") / f"permutations_{args.L}_{args.start}.npy"
        else:
            out_path = args.output
        _ensure_parent_dir(out_path)
        np.save(out_path, perms)
        print(f"Saved {perms.shape[0]} permutations for L={args.L}, start={args.start} → {out_path}")


if __name__ == "__main__":
    main()