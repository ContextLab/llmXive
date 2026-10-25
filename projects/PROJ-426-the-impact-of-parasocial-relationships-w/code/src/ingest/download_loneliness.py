"""
Download the Reddit Loneliness Longitudinal Dataset from Zenodo.

This script fetches the dataset identified by a Zenodo DOI, validates that it
contains the required columns, enforces that each user has at least
``MIN_MONTHS_PER_USER`` distinct calendar months with a non‑null
``UCLA_Loneliness_Score``, and writes the cleaned data to a Parquet file.
The script is deliberately lightweight so that the unit test
``tests/unit/test_download_loneliness.py`` can run it without additional
configuration.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

# Project‑wide utilities
from llmxive_toolkit import paths, get_logger
from src.utils.config import get_config
from src.utils.logging import log_stage_start, log_stage_end, log_error_context

# External helper for Zenodo downloads (installed in the environment)
from zenodo_get import zenodo_get

# ----------------------------------------------------------------------
# Constants – these are imported by the unit test
# ----------------------------------------------------------------------
# Minimum number of distinct calendar months with a non‑null loneliness score
MIN_MONTHS_PER_USER = 6

# Required column names in the raw dataset (as per the specification)
REQUIRED_COLUMNS = [
    "username_hash",
    "UCLA_Loneliness_Score",
    "timestamp",
    "baseline_text",
    "age",
    "gender",
]

# Minimum number of rows (after cleaning) that the dataset must contain
MIN_ROWS = 600

# Output location (used by the test)
OUTPUT_PARQUET = paths.data("raw", "loneliness_dataset.parquet")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _download_from_zenodo(doi: str, dest_dir: Path) -> Path:
    """
    Download a Zenodo record identified by ``doi`` into ``dest_dir``.
    Returns the path to the first data file (CSV or Parquet) found.
    """
    logger = get_logger(__name__)
    logger.info(f"Downloading Zenodo record {doi} into {dest_dir}")

    # ``zenodo_get`` expects a list of DOIs and a target directory.
    zenodo_get([doi], output_dir=str(dest_dir))

    # Find the first file that looks like a dataset.
    candidates = [
        p for p in dest_dir.iterdir()
        if p.suffix.lower() in {".csv", ".parquet", ".zip"}
    ]
    if not candidates:
        raise FileNotFoundError(f"No data file found after downloading DOI {doi}")

    # If a zip archive is present, extract it and look again.
    first = candidates[0]
    if first.suffix.lower() == ".zip":
        import zipfile

        with zipfile.ZipFile(first, "r") as zip_ref:
            zip_ref.extractall(dest_dir)
        extracted = [
            p for p in dest_dir.iterdir()
            if p.suffix.lower() in {".csv", ".parquet"}
        ]
        if not extracted:
            raise FileNotFoundError("Zip archive did not contain a CSV/Parquet file")
        first = extracted[0]

    logger.info(f"Dataset file resolved to {first}")
    return first

def _load_dataframe(file_path: Path) -> pd.DataFrame:
    """Load CSV or Parquet into a DataFrame."""
    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_path.suffix}")
    return df

def _validate_columns(df: pd.DataFrame) -> None:
    """Ensure all REQUIRED_COLUMNS are present."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

def _enforce_longitudinal_depth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only users that have at least ``MIN_MONTHS_PER_USER`` distinct
    calendar months with a non‑null ``UCLA_Loneliness_Score``.
    """
    # Ensure timestamp is a datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Drop rows where the score is null or timestamp could not be parsed
    mask = df["UCLA_Loneliness_Score"].notna() & df["timestamp"].notna()
    df = df[mask].copy()

    # Extract year‑month identifier
    df["year_month"] = df["timestamp"].dt.to_period("M")

    # Count distinct months per user
    month_counts = (
        df.groupby("username_hash")["year_month"]
        .nunique()
        .rename("month_count")
    )
    eligible_users = month_counts[month_counts >= MIN_MONTHS_PER_USER].index

    filtered = df[df["username_hash"].isin(eligible_users)].drop(columns=["year_month"])
    return filtered

def _final_row_count_check(df: pd.DataFrame) -> None:
    """Raise an error if the cleaned dataset is too small."""
    if len(df) < MIN_ROWS:
        raise ValueError(
            f"Dataset contains only {len(df)} rows after cleaning; "
            f"minimum required is {MIN_ROWS}."
        )

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Download, validate, clean, and persist the Reddit Loneliness Longitudinal
    Dataset.
    """
    log_stage_start("T003: Download Loneliness Dataset")
    logger = get_logger(__name__)

    try:
        # ------------------------------------------------------------------
        # Configuration – the DOI can be overridden via the global config.
        # ------------------------------------------------------------------
        cfg = get_config()
        zenodo_doi = cfg.get("data", {}).get(
            "zenodo_loneliness_doi", "10.5281/zenodo.1234567"
        )
        download_dir = Path("data") / "raw"
        download_dir.mkdir(parents=True, exist_ok=True)

        # ------------------------------------------------------------------
        # 1. Download the raw file from Zenodo
        # ------------------------------------------------------------------
        raw_file = _download_from_zenodo(zenodo_doi, download_dir)

        # ------------------------------------------------------------------
        # 2. Load into a DataFrame
        # ------------------------------------------------------------------
        df = _load_dataframe(raw_file)

        # ------------------------------------------------------------------
        # 3. Basic schema validation
        # ------------------------------------------------------------------
        _validate_columns(df)

        # ------------------------------------------------------------------
        # 4. Enforce longitudinal depth (≥ MIN_MONTHS_PER_USER months)
        # ------------------------------------------------------------------
        df = _enforce_longitudinal_depth(df)

        # ------------------------------------------------------------------
        # 5. Final row‑count sanity check
        # ------------------------------------------------------------------
        _final_row_count_check(df)

        # ------------------------------------------------------------------
        # 6. Persist cleaned data
        # ------------------------------------------------------------------
        OUTPUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(OUTPUT_PARQUET, index=False)
        logger.info(f"Cleaned dataset written to {OUTPUT_PARQUET}")

        log_stage_end("T003: Download Loneliness Dataset", success=True)

    except Exception as exc:
        log_error_context("T003: Download Loneliness Dataset", exc)
        log_stage_end("T003: Download Loneliness Dataset", success=False)
        raise

if __name__ == "__main__":
    main()
