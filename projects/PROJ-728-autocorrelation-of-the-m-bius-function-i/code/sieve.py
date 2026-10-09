"""Linear-time Möbius sieve.

This module provides a function to compute the Möbius function μ(n) for
1 ≤ n ≤ N in O(N) time using the classic linear sieve algorithm.
The result is stored as a NumPy ``int8`` array where the value at index
``i`` corresponds to μ(i) (with μ(0) unused and set to 0).

The script can be executed directly to generate the array for the
default maximum ``N = 10_000_000`` and write it to
``data/raw/mobius_array.npy``.  The command used by the quickstart is::

    python code/sieve.py --generate

The implementation is deterministic and does not rely on any external data.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np

__all__ = ["compute_mobius", "save_mobius_array"]


def compute_mobius(N: int) -> np.ndarray:
    """Compute μ(n) for 1 ≤ n ≤ N using a linear sieve.

    Parameters
    ----------
    N : int
        Upper bound (inclusive) of the range.

    Returns
    -------
    np.ndarray
        1‑dimensional ``int8`` array of length ``N + 1`` where
        ``arr[i] == μ(i)`` for ``i >= 1`` and ``arr[0] == 0``.
    """
    if N < 1:
        raise ValueError("N must be at least 1")

    # Allocate arrays
    mu = np.zeros(N + 1, dtype=np.int8)
    is_composite = np.zeros(N + 1, dtype=bool)
    primes: list[int] = []

    mu[1] = 1  # μ(1) = 1

    for i in range(2, N + 1):
        if not is_composite[i]:
            # i is prime
            primes.append(i)
            mu[i] = -1  # μ(p) = -1 for prime p

        # Iterate over primes and mark multiples
        for p in primes:
            ip = i * p
            if ip > N:
                break
            is_composite[ip] = True
            if i % p == 0:
                # p divides i -> square factor appears
                mu[ip] = 0
                break
            else:
                mu[ip] = -mu[i]

    return mu


def save_mobius_array(
    N: int,
    output_path: Path | str = Path("data/raw/mobius_array.npy"),
) -> None:
    """Compute the Möbius array and write it to ``output_path`` as ``.npy``.

    The function creates parent directories if they do not exist.

    Parameters
    ----------
    N : int
        Upper bound for the sieve.
    output_path : Path | str, optional
        Destination file path. Defaults to ``data/raw/mobius_array.npy``.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mu = compute_mobius(N)
    # Ensure dtype is int8 (already guaranteed)
    np.save(output_path, mu)
    print(f"Saved Möbius array of length {N} to {output_path}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the Möbius function array up to N and save as a NumPy .npy file."
    )
    parser.add_argument(
        "--max",
        type=int,
        default=10_000_000,
        help="Maximum integer N (inclusive) for which to compute μ(n). Default: 10,000,000.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/mobius_array.npy",
        help="Path to write the NumPy .npy file. Default: data/raw/mobius_array.npy",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="If set, compute the array and write it to the output path.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.generate:
        save_mobius_array(N=args.max, output_path=args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
