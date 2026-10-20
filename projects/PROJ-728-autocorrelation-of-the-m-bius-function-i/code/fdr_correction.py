"""
fdr_correction.py
-----------------
Implements Benjamini–Hochberg false discovery rate (FDR) correction
for the autocorrelation statistics produced by the pipeline.

The script reads ``data/processed/autocorrelation_stats.csv``,
computes BH‑adjusted p‑values from the raw ``p_value`` column,
adds a new column ``adjusted_p_value`` and overwrites the CSV.
It works even when the input CSV contains only the header (no data
rows) – in that case only the header (with the new column) is
written back.

The implementation follows the specification in the project
plan: ``statsmodels.stats.multitest.multipletests`` with
``alpha=0.05`` and the ``fdr_bh`` method.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
from statsmodels.stats.multitest import multipletests

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
INPUT_CSV = pathlib.Path("data/processed/autocorrelation_stats.csv")
ALPHA = 0.05

# ----------------------------------------------------------------------


def _ensure_parent_dir(p: pathlib.Path) -> None:
    """Create the parent directory of *p* if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)


def _read_stats(csv_path: pathlib.Path) -> pd.DataFrame:
    """Read the statistics CSV, returning a DataFrame (may be empty)."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Stats CSV not found: {csv_path}")
    # ``dtype`` is left to pandas default – it will infer types.
    return pd.read_csv(csv_path)


def _write_stats(df: pd.DataFrame, csv_path: pathlib.Path) -> None:
    """Write the DataFrame back to CSV, preserving column order."""
    _ensure_parent_dir(csv_path)
    df.to_csv(csv_path, index=False, float_format="%.12g")


def _apply_bh_correction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Benjamini–Hochberg FDR correction to the ``p_value`` column.

    The function adds a new column ``adjusted_p_value`` to the
    DataFrame.  If the DataFrame has no rows, a column header is still
    added.
    """
    if "p_value" not in df.columns:
        raise KeyError("Input CSV must contain a 'p_value' column.")

    # When there are no data rows we simply add an empty column.
    if df.empty:
        df["adjusted_p_value"] = pd.Series(dtype="float64")
        return df

    # Extract raw p‑values as a NumPy array.
    raw_pvals = df["p_value"].to_numpy()

    # ``multipletests`` returns (reject, pvals_corrected, _, _)
    _, adj_pvals, _, _ = multipletests(
        raw_pvals,
        alpha=ALPHA,
        method="fdr_bh",
    )
    # Ensure the adjusted p‑values are capped at 1.0 (the function
    # already does this, but we enforce it for safety).
    adj_pvals = adj_pvals.clip(upper=1.0)

    df["adjusted_p_value"] = adj_pvals
    return df


def main() -> None:
    """
    Entry point for the pipeline stage.

    Reads the stats CSV, adds BH‑adjusted p‑values, and overwrites the
    file.  Any exception is printed to ``stderr`` and re‑raised so
    that the orchestrator can abort the pipeline if necessary.
    """
    try:
        df = _read_stats(INPUT_CSV)
        df = _apply_bh_correction(df)
        _write_stats(df, INPUT_CSV)
        print(f"BH FDR correction applied; updated file written to {INPUT_CSV}")
    except Exception as exc:  # pragma: no cover – defensive
        print(f"[ERROR] FDR correction failed: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
