"""
Uniformity test for p-values using the Kolmogorov–Smirnov test.

This script loads the p-values produced by the null‑distribution step
(``data/processed/autocorr_stats.csv``), runs a one‑sample KS test
against the uniform distribution on [0, 1], and writes the result as a
JSON file ``data/processed/uniformity_test.json`` with the keys:

    {
        "ks_statistic": <float>,
        "p_value": <float>
    }

The script is intended to be invoked as part of the full pipeline:

    python -m code.uniformity_test

It will create any missing parent directories.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kstest

# ----------------------------------------------------------------------
# Constants – paths relative to the project root
# ----------------------------------------------------------------------
INPUT_CSV = Path("data/processed/autocorr_stats.csv")
OUTPUT_JSON = Path("data/processed/uniformity_test.json")

# ----------------------------------------------------------------------
def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
def _load_p_values(csv_path: Path) -> np.ndarray:
    """
    Load the ``p_value`` column from the CSV file.

    Parameters
    ----------
    csv_path : Path
        Path to ``autocorr_stats.csv`` produced by ``null_distribution.py``.

    Returns
    -------
    np.ndarray
        1‑D array of p‑values as ``float64``.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, usecols=["p_value"])
    # Ensure the column is numeric and drop NaNs (should not occur in valid data)
    pvals = pd.to_numeric(df["p_value"], errors="coerce").dropna().to_numpy(dtype=np.float64)

    if pvals.size == 0:
        raise ValueError("No valid p-values found in the input CSV.")
    return pvals

# ----------------------------------------------------------------------
def _run_ks_test(pvals: np.ndarray) -> tuple[float, float]:
    """
    Perform a one‑sample KS test against the uniform distribution.

    Parameters
    ----------
    pvals : np.ndarray
        Array of p‑values in the interval [0, 1].

    Returns
    -------
    tuple[float, float]
        (ks_statistic, ks_pvalue)
    """
    # The KS test expects the sample to be sorted internally; scipy handles it.
    ks_result = kstest(pvals, "uniform")
    return ks_result.statistic, ks_result.pvalue

# ----------------------------------------------------------------------
def main() -> None:
    """Entry point for ``python -m code.uniformity_test``."""
    # Load p‑values
    pvals = _load_p_values(INPUT_CSV)

    # Run KS test
    ks_stat, ks_p = _run_ks_test(pvals)

    # Prepare output JSON
    result = {
        "ks_statistic": float(ks_stat),
        "p_value": float(ks_p)
    }

    # Write JSON
    _ensure_parent_dir(OUTPUT_JSON)
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)

    print(f"KS test completed. Statistic={ks_stat:.6f}, p‑value={ks_p:.6f}")
    print(f"Result written to {OUTPUT_JSON}")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
