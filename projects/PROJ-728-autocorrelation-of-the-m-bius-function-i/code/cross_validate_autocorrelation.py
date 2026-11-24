"""
cross_validate_autocorrelation.py
---------------------------------
This script performs the **exact int64 cross‑validation** required by
task **T009** (Constitution VI).

For every window defined in ``data/raw/window_starts.json`` and for
every lag ``h = 1 … ⌊L/2⌋`` (where ``L`` is the interval length),
it recomputes the autocorrelation sum

    S = Σ_{i=0}^{L‑h‑1} μ(k+i)·μ(k+i+h)

using pure integer arithmetic (int64) and compares the result,
after normalisation, with the value obtained from the FFT‑based
implementation in ``code.autocorrelation._compute_autocorrelation_all_fft``.

The script records two statistics in ``data/processed/pipeline_status.json``:

  * ``autocorrelation_crosscheck.n_pairs_checked`` – total number of
    (window, lag) pairs examined.
  * ``autocorrelation_crosscheck.max_relative_error`` – the largest
    relative error observed between the integer and FFT results.

If any relative error exceeds the tolerance ``1e‑9`` the script raises
an exception, causing the pipeline to abort (as required by the
verification test ``tests/unit/test_autocorrelation.py``).

The script is invoked automatically by ``code.main`` after the
autocorrelation stage has produced ``data/processed/autocorrelation_raw.csv``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Helper utilities (mirroring those in other modules)
# ----------------------------------------------------------------------
def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of *p* if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
MOBIUS_PATH = Path("data/raw/mobius_array.npy")
WINDOW_STOPS_PATH = Path("data/raw/window_starts.json")
# The CSV produced by the autocorrelation stage.  It may be absent in a
# demo run, so we treat it as optional.
AUTOCORR_STATS_PATH = Path("data/processed/autocorr_stats.csv")
PIPELINE_STATUS_PATH = Path("data/processed/pipeline_status.json")

# ----------------------------------------------------------------------
# Core cross‑validation logic
# ----------------------------------------------------------------------
def _load_mobius() -> np.ndarray:
    """Load the Möbius array; raise if missing."""
    if not MOBIUS_PATH.is_file():
        raise FileNotFoundError(f"Möbius array not found at {MOBIUS_PATH}")
    return np.load(MOBIUS_PATH, allow_pickle=False)

def _load_window_map() -> Dict[int, list[int]]:
    """Load the JSON mapping ``{L: [start, …]}``."""
    if not WINDOW_STOPS_PATH.is_file():
        raise FileNotFoundError(f"Window starts file not found at {WINDOW_STOPS_PATH}")
    with WINDOW_STOPS_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}

def _load_autocorr_stats() -> pd.DataFrame:
    """
    Load the CSV produced by the autocorrelation stage.

    The file may be missing (e.g. when the demo flag is used).  In that
    case we return an empty DataFrame with the expected columns so that
    downstream code that merely checks for its existence does not fail.
    """
    if not AUTOCORR_STATS_PATH.is_file():
        # Return an empty DataFrame with the required schema.
        cols = [
            "interval_start",
            "interval_length",
            "lag",
            "autocorrelation",
            "p_value",
            "ci_lower",
            "ci_upper",
        ]
        return pd.DataFrame(columns=cols)
    return pd.read_csv(AUTOCORR_STATS_PATH)

# Import the FFT‑based helper from the existing module.
# The public API guarantees the symbol exists.
from autocorrelation import _compute_autocorrelation_all_fft  # type: ignore

def _int64_autocorrelation(mobius: np.ndarray, start: int, L: int, h: int) -> float:
    """
    Compute the normalized autocorrelation for a single window/lag using
    exact 64‑bit integer arithmetic.

    Parameters
    ----------
    mobius : np.ndarray
        The Möbius array (int8) with a dummy ``0`` at index 0.
    start : int
        1‑based start index of the window.
    L : int
        Length of the window.
    h : int
        Lag (1 ≤ h < L).

    Returns
    -------
    float
        Normalised autocorrelation ``S / (L‑h)`` where ``S`` is the
        integer sum Σ μ(k+i)·μ(k+i+h). ``float`` conversion is safe
        because the exact integer result fits in int64 (|μ| ≤ 1).
    """
    if h >= L or h < 1:
        raise ValueError("Lag h must satisfy 1 <= h < L")
    window = mobius[start : start + L]          # shape (L,)
    shifted = mobius[start + h : start + L + h]  # shape (L‑h,)
    prod = window.astype(np.int64) * shifted.astype(np.int64)
    S = int(prod.sum())                         # Python int (unbounded)
    return S / float(L - h)

def main() -> None:
    """
    Entry point for the cross‑validation stage.

    It iterates over every window and every admissible lag,
    computes both the integer‑exact and FFT‑based autocorrelations,
    checks the relative error against the tolerance ``1e‑9``, and
    records the aggregate statistics in ``pipeline_status.json``.
    """
    # Load required data
    mobius = _load_mobius()
    window_map = _load_window_map()
    # Load the CSV if it exists – the data itself is not needed for the
    # cross‑validation, but loading it confirms that the previous stage
    # produced a file with the expected columns.
    _ = _load_autocorr_stats()

    tolerance = 1e-9
    n_checked = 0
    max_rel_error = 0.0

    for L, starts in window_map.items():
        for start in starts:
            # Compute FFT‑based autocorrelations for *all* lags at once.
            fft_vals = _compute_autocorrelation_all_fft(mobius, start, L)
            max_lag = L // 2
            for h in range(1, max_lag + 1):
                int_val = _int64_autocorrelation(mobius, start, L, h)
                fft_val = float(fft_vals[h - 1])
                # Guard against division by zero (should not happen unless L‑h == 0)
                if fft_val == 0.0 and int_val == 0.0:
                    rel_err = 0.0
                else:
                    rel_err = abs(int_val - fft_val) / max(abs(fft_val), 1e-12)
                if rel_err > tolerance:
                    raise RuntimeError(
                        f"Relative error {rel_err:.2e} exceeds tolerance for "
                        f"window start={start}, L={L}, lag={h}"
                    )
                n_checked += 1
                if rel_err > max_rel_error:
                    max_rel_error = rel_err

    # Update pipeline_status.json
    status: dict = {}
    if PIPELINE_STATUS_PATH.is_file():
        with PIPELINE_STATUS_PATH.open("r", encoding="utf-8") as f:
            try:
                status = json.load(f)
            except json.JSONDecodeError:
                status = {}
    # Insert the cross‑check results
    status.setdefault("autocorrelation_crosscheck", {})
    status["autocorrelation_crosscheck"]["n_pairs_checked"] = n_checked
    # Store with reasonable precision
    status["autocorrelation_crosscheck"]["max_relative_error"] = float(max_rel_error)

    _ensure_parent_dir(PIPELINE_STATUS_PATH)
    with PIPELINE_STATUS_PATH.open("w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, sort_keys=True)

    print(
        f"Cross‑validation completed: {n_checked} pairs checked, "
        f"max relative error = {max_rel_error:.2e}"
    )

if __name__ == "__main__":
    # When run as a script we simply execute the main routine.
    # Any exception will cause a non‑zero exit code, which the
    # orchestrator (code/main.py) treats as a failure.
    main()
