"""
fdr_correction.py
-----------------
Apply Benjamini–Hochberg FDR correction to the raw p‑values produced by the
permutation stage.

The script reads ``data/processed/autocorr_stats.csv`` (the CSV generated
by ``code.null_distribution``), adds a new column ``adjusted_p_value`` that
contains the BH‑adjusted p‑values, and overwrites the CSV in place.

It is invoked from the pipeline orchestrator (``code.main``) via the
``fdr_main`` callable imported from this module.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
from statsmodels.stats.multitest import multipletests

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _ensure_parent_dir(p: pathlib.Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)


def _read_stats(csv_path: pathlib.Path) -> pd.DataFrame:
    """
    Load the statistics CSV.

    Parameters
    ----------
    csv_path : pathlib.Path
        Path to the CSV file produced by ``null_distribution``.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the CSV contents.  If the file exists but
        contains only a header, an empty DataFrame with the correct column
        order is returned.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Statistics CSV not found: {csv_path}")

    # ``read_csv`` will correctly handle a header‑only file, yielding an
    # empty DataFrame with the appropriate columns.
    df = pd.read_csv(csv_path)
    return df


def _apply_bh_correction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Benjamini–Hochberg FDR correction to the ``p_value`` column.

    The function adds a new column ``adjusted_p_value`` to ``df``.  If the
    DataFrame has no rows, the column header is still added (as required
    by the unit tests).

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame that must contain a ``p_value`` column.

    Returns
    -------
    pandas.DataFrame
        The same DataFrame with an additional ``adjusted_p_value`` column.
    """
    if "p_value" not in df.columns:
        raise ValueError("Input DataFrame must contain a 'p_value' column.")

    # When there are no rows we still create the column with an empty Series.
    if df.empty:
        df["adjusted_p_value"] = pd.Series(dtype="float64")
        return df

    # ``multipletests`` expects a 1‑D array of p‑values.
    raw_p = df["p_value"].to_numpy()
    # Apply BH correction (alpha is irrelevant for the adjusted values;
    # we use the default 0.05 to stay close to the literature).
    _, adj_p, _, _ = multipletests(raw_p, alpha=0.05, method="fdr_bh")
    df["adjusted_p_value"] = adj_p
    return df


def _write_stats(df: pd.DataFrame, csv_path: pathlib.Path) -> None:
    """
    Write the DataFrame back to CSV, preserving column order.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to write.
    csv_path : pathlib.Path
        Destination path.
    """
    _ensure_parent_dir(csv_path)
    # Preserve the original column order, inserting the new column just
    # after the raw ``p_value`` column for readability.
    if "adjusted_p_value" in df.columns:
        cols = list(df.columns)
        # Ensure ``adjusted_p_value`` appears after ``p_value``.
        if "p_value" in cols:
            p_idx = cols.index("p_value")
            # Remove any existing occurrence and re‑insert.
            cols.pop(cols.index("adjusted_p_value"))
            cols.insert(p_idx + 1, "adjusted_p_value")
        df = df[cols]

    df.to_csv(csv_path, index=False, float_format="%.12g")


def main() -> None:
    """
    Entry point for the FDR‑correction stage.

    The function reads the CSV written by the null‑distribution step,
    applies the Benjamini–Hochberg correction, and overwrites the CSV.
    Any exception is printed to ``stderr`` and re‑raised so that the
    orchestrator can abort the pipeline if necessary.
    """
    # The CSV path is fixed by the rest of the pipeline.
    csv_path = pathlib.Path("data/processed/autocorr_stats.csv")

    try:
        df = _read_stats(csv_path)
    except Exception as exc:
        print(f"[ERROR] Failed to read statistics CSV: {exc}", file=sys.stderr)
        raise

    try:
        df = _apply_bh_correction(df)
    except Exception as exc:
        print(f"[ERROR] BH correction failed: {exc}", file=sys.stderr)
        raise

    try:
        _write_stats(df, csv_path)
    except Exception as exc:
        print(f"[ERROR] Failed to write corrected CSV: {exc}", file=sys.stderr)
        raise

    print(f"Benjamini–Hochberg FDR correction applied; output written to {csv_path}")


if __name__ == "__main__":
    # Allow running the module directly for debugging.
    main()