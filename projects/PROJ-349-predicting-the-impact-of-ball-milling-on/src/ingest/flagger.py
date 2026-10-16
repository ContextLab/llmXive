"""
Flagger utility for unstructured Particle Size Distribution (PSD) entries.

This module provides a function to identify rows in a dataset where the PSD
metrics (d10, d50, d90) are missing or unstructured (e.g., represented as
NaN, None, or empty strings). Such rows are logged to a persistent file
`data/flagged_psd.log` for later manual curation or OCR fallback processing.

The function returns the number of flagged rows, enabling downstream steps
to make decisions based on the presence of unstructured PSD data.
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Columns that constitute structured PSD data.
PSD_COLUMNS = ["d10", "d50", "d90"]


def _is_unstructured(series: pd.Series) -> bool:
    """
    Determine if a PSD column entry is unstructured.

    An entry is considered unstructured if it is NaN, None, or an empty
    string after stripping whitespace.

    Parameters
    ----------
    series : pd.Series
        A pandas Series representing a column of PSD values.

    Returns
    -------
    bool
        True if the column contains any unstructured entries.
    """
    # pandas treats None and NaN similarly; isna covers both.
    if series.isna().any():
        return True
    # Check for empty strings (including strings that are whitespace only).
    if series.astype(str).str.strip().eq("").any():
        return True
    return False


def flag_unstructured_psd(df: pd.DataFrame) -> int:
    """
    Identify and log rows with unstructured PSD entries.

    Rows are flagged when any of the PSD columns (d10, d50, d90) are
    missing or empty. The function appends a line for each flagged
    experiment to ``data/flagged_psd.log`` and returns the total count.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset to inspect. Expected to contain at least the columns
        listed in :data:`PSD_COLUMNS`. An ``experiment_id`` column is used
        for logging; if absent, the row index is logged instead.

    Returns
    -------
    int
        Number of rows flagged as having unstructured PSD data.
    """
    missing_columns = [col for col in PSD_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"DataFrame is missing required PSD columns: {missing_columns}"
        )

    # Identify rows where any PSD column is unstructured.
    mask = df[PSD_COLUMNS].apply(_is_unstructured, axis=0).any(axis=1)
    flagged_df = df[mask]

    count = len(flagged_df)
    if count == 0:
        log.info("No unstructured PSD entries found.")
        return 0

    # Resolve the log file path; the helper creates parent directories.
    log_path: Path = paths.data("flagged_psd.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare log lines.
    lines = []
    if "experiment_id" in df.columns:
        for exp_id in flagged_df["experiment_id"]:
            lines.append(f"{exp_id}\n")
    else:
        # Fallback to using the DataFrame index.
        for idx in flagged_df.index:
            lines.append(f"index_{idx}\n")

    # Append to the log file.
    with log_path.open("a", encoding="utf-8") as f:
        f.writelines(lines)

    log.info(
        "Flagged %d rows with unstructured PSD data; entries written to %s",
        count,
        log_path,
    )
    return count


# Optional CLI entry point for ad‑hoc usage.
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Flag rows with unstructured PSD entries in a CSV/Parquet file."
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to the dataset file (CSV or Parquet).",
    )
    args = parser.parse_args()

    # Load the dataset based on file extension.
    try:
        if args.input_path.suffix.lower() in {".csv"}:
            df_input = pd.read_csv(args.input_path)
        elif args.input_path.suffix.lower() in {".parquet", ".pq"}:
            df_input = pd.read_parquet(args.input_path)
        else:
            raise ValueError(
                f"Unsupported file extension: {args.input_path.suffix}"
            )
    except Exception as e:
        log.error("Failed to load dataset: %s", e)
        sys.exit(1)

    try:
        flagged = flag_unstructured_psd(df_input)
        log.info("Total flagged rows: %d", flagged)
    except Exception as e:
        log.error("Error during flagging: %s", e)
        sys.exit(1)