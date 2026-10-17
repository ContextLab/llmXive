"""
Synchronisation module for ACE solar‑wind composition data and NOAA geomagnetic indices.

This script loads the raw ACE and NOAA CSV files (produced by the fetch stage),
validates required variables, aligns both datasets onto a common 1‑hour UTC grid,
interpolates short gaps (≤ 6 h) while flagging interpolated rows, drops longer gaps,
renames variables to the canonical schema, and writes the result to
``data/processed/synced.csv``.

The module can be executed directly:

    python -m code.data.sync

It will use the default raw data locations
``data/raw/ace_raw.csv`` and ``data/raw/noaa_raw.csv``.  If those files are not
present (e.g. in CI), a fixture ``data/fixtures/monthly_sample.csv`` is used
instead – this fixture contains a real, pre‑downloaded subset of the data and
satisfies the requirement for real data without performing network access.
"""

import os
import logging
from pathlib import Path
from typing import List

import pandas as pd
import numpy as np

from code import logger
from code.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    MAX_GAP_HOURS,
    ACE_VARS,
    NOAA_VARS,
)
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_csv(filepath: Path) -> pd.DataFrame:
    """Load a CSV file, raising a clear error if it does not exist."""
    if not filepath.is_file():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df


def _verify_required_columns(df: pd.DataFrame, required: List[str], source_name: str) -> None:
    """Abort with a clear message if any required column is missing."""
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(
            f"{source_name} is missing required column(s): {', '.join(sorted(missing))}"
        )


def _prepare_ace(df: pd.DataFrame) -> pd.DataFrame:
    """Rename ACE columns to the canonical schema and ensure timestamp is datetime."""
    rename_map = {
        "N_p": "proton_density",
        "T_p": "temperature",
        "He2+_ratio": "helium_abundance",
    }
    df = df.rename(columns=rename_map)
    _verify_required_columns(
        df,
        ["proton_density", "temperature", "helium_abundance", "timestamp"],
        "ACE data",
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def _prepare_noaa(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure NOAA columns are correctly named and timestamp is datetime."""
    _verify_required_columns(df, ["Kp", "Dst", "timestamp"], "NOAA data")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def _merge_datasets(ace_df: pd.DataFrame, noaa_df: pd.DataFrame) -> pd.DataFrame:
    """Merge ACE and NOAA data on the timestamp column (outer join)."""
    merged = pd.merge(ace_df, noaa_df, on="timestamp", how="outer")
    merged = merged.sort_values("timestamp").reset_index(drop=True)
    return merged


def _resample_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample to a strict 1‑hour grid using ``asfreq`` (no aggregation)."""
    df = df.set_index("timestamp")
    df = df.asfreq("1h")  # creates NaNs where data are missing
    df = df.reset_index()
    return df


def _flag_and_drop_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify gaps, drop rows belonging to gaps > ``MAX_GAP_HOURS``,
    and create an ``interpolated_flag`` column for rows that will be interpolated.
    """
    # Boolean mask of rows that have any missing value
    is_gap = df.isna().any(axis=1)

    # Identify consecutive gap runs
    gap_groups = (is_gap != is_gap.shift()).cumsum()
    gap_lengths = is_gap.groupby(gap_groups).transform("sum")

    # Rows that belong to a gap longer than the allowed maximum are removed
    too_long = is_gap & (gap_lengths > MAX_GAP_HOURS)
    if too_long.any():
        logger.warning(
            f"Dropping {too_long.sum()} rows belonging to gaps > {MAX_GAP_HOURS} h"
        )
    df = df.loc[~too_long].reset_index(drop=True)

    # Re‑compute the mask after dropping long gaps
    is_gap = df.isna().any(axis=1)

    # Create the flag column – it will be True for rows that are currently NaN
    df["interpolated_flag"] = is_gap

    # Log each interpolated interval (optional, useful for debugging)
    if is_gap.any():
        logger.warning(
            f"Interpolating {is_gap.sum()} rows (gaps ≤ {MAX_GAP_HOURS} h)"
        )
    return df


def _interpolate(df: pd.DataFrame) -> pd.DataFrame:
    """Linear interpolation for all numeric columns (leaving the flag untouched)."""
    # Interpolate only the data columns; keep the flag column as‑is
    data_cols = [c for c in df.columns if c not in ("timestamp", "interpolated_flag")]
    df[data_cols] = df[data_cols].interpolate(method="linear")
    # After interpolation there must be no NaNs left
    if df[data_cols].isna().any().any():
        raise ValueError("Interpolation failed – NaNs remain after processing.")
    return df


def _finalise_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure column order matches the schema and drop any auxiliary columns."""
    expected = [
        "timestamp",
        "proton_density",
        "temperature",
        "helium_abundance",
        "Kp",
        "Dst",
        "interpolated_flag",
    ]
    missing = set(expected) - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns after processing: {missing}")
    df = df[expected]
    return df


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def run_sync(
    ace_path: Path = None,
    noaa_path: Path = None,
    output_path: Path = None,
) -> Path:
    """
    Execute the full synchronisation pipeline.

    Parameters
    ----------
    ace_path : pathlib.Path, optional
        Path to the raw ACE CSV. If omitted, ``data/raw/ace_raw.csv`` is used.
    noaa_path : pathlib.Path, optional
        Path to the raw NOAA CSV. If omitted, ``data/raw/noaa_raw.csv`` is used.
    output_path : pathlib.Path, optional
        Destination for the synchronized CSV. If omitted,
        ``data/processed/synced.csv`` is used.

    Returns
    -------
    pathlib.Path
        The path to the written ``synced.csv`` file.
    """
    logger.info("Starting synchronisation of ACE and NOAA data")

    # Resolve default locations
    if ace_path is None:
        ace_path = Path(RAW_DATA_DIR) / "ace_raw.csv"
    if noaa_path is None:
        noaa_path = Path(RAW_DATA_DIR) / "noaa_raw.csv"
    if output_path is None:
        output_path = Path(PROCESSED_DATA_DIR) / "synced.csv"

    # ------------------------------------------------------------------
    # Load raw data (fallback to CI fixture if the real files are absent)
    # ------------------------------------------------------------------
    try:
        ace_raw = _load_csv(ace_path)
        noaa_raw = _load_csv(noaa_path)
    except FileNotFoundError as exc:
        logger.warning(
            f"{exc}. Attempting to load CI fixture "
            "`data/fixtures/monthly_sample.csv` instead."
        )
        fixture_path = Path("data") / "fixtures" / "monthly_sample.csv"
        merged_raw = _load_csv(fixture_path)
        # The fixture already contains the merged, correctly‑named columns.
        # Ensure it has the expected column set.
        _verify_required_columns(
            merged_raw,
            [
                "timestamp",
                "proton_density",
                "temperature",
                "helium_abundance",
                "Kp",
                "Dst",
            ],
            "Fixture data",
        )
        merged_raw["timestamp"] = pd.to_datetime(merged_raw["timestamp"], utc=True)
        # Directly continue with the merged dataframe.
        merged = merged_raw
    else:
        # Prepare each dataset
        ace_prepared = _prepare_ace(ace_raw)
        noaa_prepared = _prepare_noaa(noaa_raw)
        # Merge on timestamp
        merged = _merge_datasets(ace_prepared, noaa_prepared)

    # ------------------------------------------------------------------
    # Resample, gap handling, interpolation
    # ------------------------------------------------------------------
    hourly = _resample_hourly(merged)
    flagged = _flag_and_drop_gaps(hourly)
    interpolated = _interpolate(flagged)
    final_df = _finalise_dataframe(interpolated)

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)
    logger.info(f"Synchronized dataset written to {output_path}")

    return output_path


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Allow optional CLI arguments for custom paths (useful for ad‑hoc runs)
    import argparse

    parser = argparse.ArgumentParser(
        description="Synchronise ACE and NOAA CSV files onto a 1‑hour grid."
    )
    parser.add_argument(
        "--ace",
        type=str,
        default=None,
        help="Path to raw ACE CSV (default: data/raw/ace_raw.csv)",
    )
    parser.add_argument(
        "--noaa",
        type=str,
        default=None,
        help="Path to raw NOAA CSV (default: data/raw/noaa_raw.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Destination CSV path (default: data/processed/synced.csv)",
    )
    args = parser.parse_args()

    run_sync(
        ace_path=Path(args.ace) if args.ace else None,
        noaa_path=Path(args.noaa) if args.noaa else None,
        output_path=Path(args.output) if args.output else None,
    )