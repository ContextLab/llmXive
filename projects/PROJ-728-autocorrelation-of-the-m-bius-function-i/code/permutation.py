"""
permutation.py
---------------
Implements block‑permutation generation for a window of the Möbius sequence
(used by unit tests) **and** a full‑pipeline engine that generates the
null distribution required by task T007.

The original implementation already provided ``generate_permutations`` and a
``--run`` mode that iterates over all windows defined in
``data/raw/window_starts.json``.  The quick‑start script, however, invoked the
module with the arguments ``--stats <output_csv> --array <mobius_npy>``,
which were not recognised.  This patch adds support for those arguments
while preserving the original behaviour.

In pipeline mode the script:
  1. Loads the Möbius array.
  2. Loads the deterministic window index (``window_starts.json``).
  3. For every window it:
     * Computes the observed autocorrelations for all lags via the FFT
       helper from ``code.autocorrelation``.
     * Generates **exactly 1 000** zero‑preserving sign permutations
       (zeros stay at their original indices, the signs of the non‑zero
       entries are uniformly shuffled).  The RNG seed is
       ``20231017 + window_id`` where ``window_id`` is a zero‑based counter
       over all windows.
     * Computes autocorrelations for all permutations in a single
       vectorised FFT call.
     * Derives a two‑sided p‑value with the “+1” correction, the
       2.5 % / 97.5 % confidence interval, and records the zero count.
     * Writes one CSV row per lag, conforming to
       ``contracts/mobius_stats.schema.yaml``.  Columns that are not yet
       available (``adjusted_p_value`` and ``sensitivity_flag``) are filled
       with placeholder values that satisfy the schema; later stages replace
       them.
  4. Writes the CSV header (and rows) to the path supplied via ``--stats``.
     For compatibility with the rest of the code base the file is also
     copied to ``data/processed/autocorr_stats.csv`` if a different path was
     requested.

The legacy block‑permutation mode (``--run``) is unchanged, and the unit
tests in ``tests/unit/test_permutation.py`` continue to pass.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import shutil
from pathlib import Path
from typing import Optional

import numpy as np

__all__ = [
    "generate_permutations",
    "generate_zero_preserving_permutations",
    "main",
]


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
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
    block_size.
    """
    if block_size <= 0:
        raise ValueError("block_size must be a positive integer.")
    n = len(window)
    blocks = [
        window[i : min(i + block_size, n)] for i in range(0, n, block_size)
    ]
    return blocks


# ----------------------------------------------------------------------
# Public API – legacy block‑permutation generator
# ----------------------------------------------------------------------
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
        # Truncate/pad just in case (should not happen)
        if permuted_window.shape[0] != L:
            permuted_window = permuted_window[:L]
        perms[i] = permuted_window

    return perms


# ----------------------------------------------------------------------
# New API – zero‑preserving sign permutations (pipeline mode)
# ----------------------------------------------------------------------
def generate_zero_preserving_permutations(
    window: np.ndarray,
    n_permutations: int,
    seed: int,
) -> np.ndarray:
    """
    Generate permutations that keep zero positions fixed and uniformly
    shuffle the signs of the non‑zero entries.

    Parameters
    ----------
    window : np.ndarray
        1‑D array of length ``L`` containing values in ``{-1, 0, 1}``.
    n_permutations : int
        Number of permutations to generate (must be 1000 for the
        specification).
    seed : int
        Seed for the RNG; the specification requires a deterministic seed
        per window (``20231017 + window_id``).

    Returns
    -------
    np.ndarray
        Array of shape ``(n_permutations, L)`` with the required
        permutations.
    """
    if n_permutations <= 0:
        raise ValueError("n_permutations must be positive")
    # Boolean mask of zero positions – these stay untouched.
    zero_mask = window == 0
    # Extract the mutable sign entries.
    signs = window[~zero_mask]

    rng = np.random.default_rng(seed)

    perms = np.empty((n_permutations, len(window)), dtype=window.dtype)

    for i in range(n_permutations):
        shuffled = rng.permutation(signs)
        # Build the permuted window: zeros stay, shuffled signs fill the rest.
        new_win = np.empty_like(window)
        new_win[zero_mask] = 0
        new_win[~zero_mask] = shuffled
        perms[i] = new_win

    return perms


# ----------------------------------------------------------------------
# I/O helpers for the pipeline mode
# ----------------------------------------------------------------------
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
    return {int(k): v for k, v in raw.items()}


def _write_stats_header(output_path: Path) -> None:
    """
    Write the CSV header required by ``contracts/mobius_stats.schema.yaml``.
    The function does *not* write any data rows.
    """
    header = [
        "interval_start",
        "interval_length",
        "lag",
        "autocorrelation",
        "p_value",
        "adjusted_p_value",
        "ci_lower",
        "ci_upper",
        "zero_count",
        "sensitivity_flag",
        "theoretical_variance",
    ]
    _ensure_parent_dir(output_path)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)


# ----------------------------------------------------------------------
# Pipeline implementation
# ----------------------------------------------------------------------
def _process_window(
    mobius: np.ndarray,
    start: int,
    L: int,
    window_id: int,
    writer: csv.writer,
    n_permutations: int = 1000,
    block_size: int = 100,
) -> None:
    """
    Process a single window: compute observed autocorrelations, generate the
    null distribution, and write one CSV row per lag.

    Parameters
    ----------
    mobius : np.ndarray
        Full Möbius array (int8) with dummy 0 at index 0.
    start : int
        1‑based window start.
    L : int
        Window length.
    window_id : int
        Deterministic identifier used to seed the RNG
        (seed = 20231017 + window_id).
    writer : csv.writer
        Writer object already positioned after the header.
    n_permutations : int
        Number of permutations (fixed to 1000 by the spec).
    block_size : int
        Block size used for the *legacy* block‑permutation mode; retained
        here only for API compatibility (not used for the zero‑preserving
        permutations).
    """
    # ------------------------------------------------------------------
    # 1. Extract the window and basic statistics.
    # ------------------------------------------------------------------
    window = mobius[start : start + L]
    zero_count = int(np.count_nonzero(window == 0))

    # If the window is all zeros the autocorrelation is undefined; we write
    # NaNs for the statistical columns and skip permutation generation.
    if zero_count == L:
        obs_autocorrs = np.full(L // 2, np.nan, dtype=float)
    else:
        # ----------------------------------------------------------------
        # 2. Observed autocorrelations (FFT‑based, via the public helper).
        # ----------------------------------------------------------------
        from autocorrelation import _compute_autocorrelation_all_fft  # local import to avoid circular deps

        obs_autocorrs = _compute_autocorrelation_all_fft(mobius, start, L)

    # ------------------------------------------------------------------
    # 3. Generate the null distribution (zero‑preserving permutations).
    # ------------------------------------------------------------------
    if zero_count == L:
        # No permutations needed – all values are zero.
        perm_ac_matrix = np.zeros((n_permutations, L // 2), dtype=float)
    else:
        seed = 20231017 + window_id
        perms = generate_zero_preserving_permutations(
            window, n_permutations=n_permutations, seed=seed
        )
        # Vectorised autocorrelation computation – reuse the function from
        # ``sensitivity.py`` which works on a (n_seq, L) array.
        from sensitivity import _compute_autocorrelations_vectorized

        perm_ac_matrix = _compute_autocorrelations_vectorized(perms, L)

    # ------------------------------------------------------------------
    # 4. Theoretical variance (sigma^2 / L) – sigma^2 = (6/pi^2)*(1-6/pi^2).
    # ------------------------------------------------------------------
    sigma2 = (6.0 / np.pi ** 2) * (1.0 - 6.0 / np.pi ** 2)
    theoretical_variance = sigma2 / L

    # ------------------------------------------------------------------
    # 5. Write one row per lag.
    # ------------------------------------------------------------------
    max_lag = L // 2
    for lag_idx in range(max_lag):
        lag = lag_idx + 1
        obs = float(obs_autocorrs[lag_idx]) if not np.isnan(obs_autocorrs[lag_idx]) else np.nan

        # Null distribution for this lag.
        null_vals = perm_ac_matrix[:, lag_idx]

        # Two‑sided p‑value with +1 correction.
        if np.isnan(obs):
            p_val = np.nan
        else:
            p_val = (np.sum(np.abs(null_vals) >= np.abs(obs)) + 1) / (n_permutations + 1)

        # Clamp extreme p‑values as required by the spec.
        if not np.isnan(p_val):
            if p_val < 0.001:
                p_val = 0.001
            elif p_val > 0.999:
                p_val = 0.999

        # Confidence interval (percentiles).
        ci_lower = float(np.percentile(null_vals, 2.5))
        ci_upper = float(np.percentile(null_vals, 97.5))

        # Placeholder values for columns that will be filled later.
        adjusted_p = 0.5  # placeholder within (0,1)
        sensitivity_flag = "stable"  # will be overwritten by sensitivity stage

        writer.writerow(
            [
                start,
                L,
                lag,
                obs,
                p_val,
                adjusted_p,
                ci_lower,
                ci_upper,
                zero_count,
                sensitivity_flag,
                theoretical_variance,
            ]
        )


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point.

    The script now supports two modes:

    1. **Legacy block‑permutation mode** (unchanged):
       ``python -m code.permutation --L <L> --start <start> [--output <path>]``

    2. **Pipeline mode**:
       ``python -m code.permutation --stats <stats_csv> --array <mobius_npy>``
    """
    parser = argparse.ArgumentParser(
        description="Generate block‑permuted Möbius windows or produce a "
        "pipeline‑compatible stats CSV."
    )
    # Legacy arguments
    parser.add_argument("--L", type=int, help="Length of the window (required unless --run is used).")
    parser.add_argument("--start", type=int, help="1‑based start index of the window (required unless --run is used).")
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
    # New pipeline‑compatible arguments
    parser.add_argument(
        "--stats",
        type=Path,
        default=None,
        help="Path to the output statistics CSV (pipeline mode).",
    )
    parser.add_argument(
        "--array",
        type=Path,
        default=None,
        help="Path to the Möbius array (pipeline mode).",
    )

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Pipeline mode: write a full statistics CSV.
    # ------------------------------------------------------------------
    if args.stats is not None and args.array is not None:
        # Load the Möbius array – will raise if the path is wrong.
        mobius = _load_mobius_array(args.array)

        # Load window definitions.
        window_map = _load_window_starts()

        # Prepare CSV file.
        _write_stats_header(args.stats)
        with args.stats.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)

            # Enumerate windows to obtain a deterministic window_id.
            window_id = 0
            for L, starts in sorted(window_map.items()):
                for start in starts:
                    _process_window(
                        mobius=mobius,
                        start=start,
                        L=L,
                        window_id=window_id,
                        writer=writer,
                        n_permutations=1000,
                        block_size=args.block_size,
                    )
                    window_id += 1

        print(f"Created statistics CSV at {args.stats}")

        # ------------------------------------------------------------------
        # Compatibility shim: many downstream modules expect the file to be
        # named ``autocorr_stats.csv``.  If the user supplied a different
        # name, copy the file to the canonical location.
        # ------------------------------------------------------------------
        canonical_path = Path("data/processed/autocorr_stats.csv")
        if canonical_path.resolve() != args.stats.resolve():
            _ensure_parent_dir(canonical_path)
            shutil.copyfile(args.stats, canonical_path)
            print(f"Copied CSV to canonical location {canonical_path}")

        return

    # ------------------------------------------------------------------
    # Legacy block‑permutation functionality (unchanged).
    # ------------------------------------------------------------------
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
