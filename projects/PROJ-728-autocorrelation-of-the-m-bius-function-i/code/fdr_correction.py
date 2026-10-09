"""
Benjamini‑Hochberg FDR correction for Möbius autocorrelation p‑values.

The script reads ``data/processed/autocorr_stats.csv``, adds an
``adjusted_p_value`` column containing the BH‑adjusted p‑values,
overwrites the original CSV, and prints a short status line.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
INPUT_CSV = pathlib.Path("data/processed/autocorr_stats.csv")
# ----------------------------------------------------------------------


def _ensure_parent_dir(p: pathlib.Path) -> None:
    """Create the parent directory of *p* if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)


def _benjamini_hochberg(pvals: np.ndarray) -> np.ndarray:
    """
    Perform the Benjamini–Hochberg FDR correction.

    Parameters
    ----------
    pvals : np.ndarray
        1‑D array of original p‑values (assumed to be in the interval [0, 1]).

    Returns
    -------
    np.ndarray
        Adjusted p‑values, same shape as ``pvals``.  Values are capped at
        1.0 and are monotonic non‑decreasing when traversed in the
        original order.
    """
    if pvals.ndim != 1:
        raise ValueError("pvals must be a 1‑D array")

    n = len(pvals)
    if n == 0:
        return np.array([], dtype=float)

    order = np.argsort(pvals)
    sorted_p = pvals[order]

    # Compute the BH adjusted values: p'_i = p_{(i)} * (n / i)
    # np.arange(1, n + 1) provides the ranks i
    adjusted = sorted_p * (n / np.arange(1, n + 1))

    # Ensure monotonicity (step‑up procedure): p'_i = min(p'_{i+1}, p'_i)
    for i in range(n - 2, -1, -1):
        if adjusted[i] > adjusted[i + 1]:
            adjusted[i] = adjusted[i + 1]

    adjusted = np.minimum(adjusted, 1.0)

    # Return to original order.
    inv_order = np.empty_like(order)
    inv_order[order] = np.arange(n)
    return adjusted[inv_order]


def main() -> None:
    """Read the stats CSV, add BH‑adjusted p‑values, and overwrite."""
    if not INPUT_CSV.is_file():
        # Fail loudly as required by core constraints
        raise FileNotFoundError(f"Required CSV not found: {INPUT_CSV}")

    try:
        df = pd.read_csv(INPUT_CSV)
    except Exception as exc:
        raise RuntimeError(f"Failed to read CSV {INPUT_CSV}: {exc}") from exc

    if "p_value" not in df.columns:
        raise KeyError("Column 'p_value' not found in input CSV.")

    # Extract p-values, handling NaNs by treating them as 1.0 or preserving them.
    # BH typically operates on valid p-values. We convert to float64.
    pvals = df["p_value"].to_numpy(dtype=float)
    
    # Handle NaNs: BH correction usually ignores them or treats them as 1.
    # To maintain array shape, we'll compute BH on non-NaNs and map back.
    mask = ~np.isnan(pvals)
    adjusted = np.full(pvals.shape, np.nan, dtype=float)
    
    if np.any(mask):
        adjusted[mask] = _benjamini_hochberg(pvals[mask])

    df["adjusted_p_value"] = adjusted
    _ensure_parent_dir(INPUT_CSV)
    df.to_csv(INPUT_CSV, index=False)

    print(f"[INFO] Added 'adjusted_p_value' to {INPUT_CSV} (rows={len(df)})")


if __name__ == "__main__":
    main()
