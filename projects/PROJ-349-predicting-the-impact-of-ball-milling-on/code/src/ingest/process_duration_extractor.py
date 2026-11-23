"""
Process Duration Extractor
-------------------------

This module ensures that the merged ball‑milling dataset contains a
``process_duration`` column.  If the column is missing it is added with
``NaN`` values.  If the dataset already contains ``start_timestamp`` and
``end_timestamp`` columns (ISO‑8601 strings or pandas timestamps) the
duration in **seconds** is computed and stored in ``process_duration``.
The resulting DataFrame is written back to the same Parquet file used by
the merge step (``data/raw/merged_dataset_temp.parquet``).

The script can be run directly::

    python -m src.ingest.process_duration_extractor

It logs progress to the standard logger and fails loudly on any I/O
problems, complying with the “REAL DATA ONLY” policy.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import numpy as np

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_merged_dataset() -> pd.DataFrame:
    """
    Load the merged dataset produced by ``src.ingest.merge``.
    The expected location is ``data/raw/merged_dataset_temp.parquet``.
    """
    merged_path = paths.data("raw", "merged_dataset_temp.parquet")
    if not merged_path.is_file():
        log.error(f"Merged dataset not found at {merged_path}")
        raise FileNotFoundError(f"Merged dataset not found at {merged_path}")

    log.info(f"Loading merged dataset from {merged_path}")
    try:
        df = pd.read_parquet(merged_path)
    except Exception as e:
        log.error(f"Failed to read parquet file: {e}")
        raise

    return df


def _compute_duration_from_timestamps(df: pd.DataFrame) -> pd.Series:
    """
    Compute duration (in seconds) from ``start_timestamp`` and
    ``end_timestamp`` columns when they exist.

    The timestamps may be strings or pandas ``datetime`` objects.
    Missing or unparsable values result in ``np.nan``.
    """
    if {"start_timestamp", "end_timestamp"}.issubset(df.columns):
        # Ensure proper datetime conversion
        start = pd.to_datetime(df["start_timestamp"], errors="coerce")
        end = pd.to_datetime(df["end_timestamp"], errors="coerce")
        duration = (end - start).dt.total_seconds()
        # Replace negative or zero durations with NaN (invalid)
        duration = duration.where(duration > 0, np.nan)
        return duration
    return pd.Series([np.nan] * len(df), index=df.index)


def extract_process_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the ``process_duration`` column exists.

    If the column is already present the function leaves it untouched
    (except for possible overwriting with computed values when timestamps
    are available).  If it is missing, the column is added.  When
    ``start_timestamp`` and ``end_timestamp`` are present, their difference
    is used to fill missing values.

    Parameters
    ----------
    df : pd.DataFrame
        The merged dataset.

    Returns
    -------
    pd.DataFrame
        The dataset with a guaranteed ``process_duration`` column.
    """
    if "process_duration" in df.columns:
        log.debug("process_duration column already present.")
        # Optionally fill missing values from timestamps
        missing_mask = df["process_duration"].isna()
        if missing_mask.any():
            log.debug(
                f"Filling {missing_mask.sum()} missing process_duration values from timestamps."
            )
            df.loc[missing_mask, "process_duration"] = _compute_duration_from_timestamps(
                df.loc[missing_mask]
            )
    else:
        log.debug("Adding missing process_duration column (filled with NaN).")
        df["process_duration"] = np.nan

        # Attempt to compute from timestamps if they exist
        df["process_duration"] = _compute_duration_from_timestamps(df)

    return df


def _save_dataset(df: pd.DataFrame) -> None:
    """
    Write the updated DataFrame back to the original parquet file.
    """
    output_path = paths.data("raw", "merged_dataset_temp.parquet")
    # Ensure parent directory exists (paths.data already creates it)
    try:
        df.to_parquet(output_path, index=False)
        log.info(f"Saved dataset with process_duration to {output_path}")
    except Exception as e:
        log.error(f"Failed to write parquet file: {e}")
        raise


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> int:
    """
    CLI entry point.

    Returns
    -------
    int
        Exit code (0 on success, non‑zero on failure).
    """
    try:
        df = _load_merged_dataset()
        df = extract_process_duration(df)
        _save_dataset(df)
        return 0
    except Exception as e:
        log.exception(f"process_duration_extractor failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())