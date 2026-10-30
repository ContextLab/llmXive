"""
Download the Reddit Loneliness Longitudinal Dataset from Zenodo,
validate required columns, enforce longitudinal depth, and write it to Parquet.

This script is invoked by `src/main.py --mode ingest_and_match`.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from datetime import datetime

# Add project root to sys.path when run as a script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import utilities
from src.utils.logging import get_logger, log_stage_start, log_stage_end, log_error_context
from src.utils.config import get_config
from src.utils.data_validation import record_checksum, ValidationError

# Import zenodo_get – the package exposes a module with a `zenodo_get` function.
# The original import `from zenodo_get import zenodo_get` raised ImportError,
# so we import the module and access the function via attribute.
import zenodo_get as _zenodo_get

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Required columns as defined in the specification.
REQUIRED_COLUMNS = [
    "username_hash",
    "UCLA_Loneliness_Score",
    "timestamp",
    "baseline_text",
    "age",
    "gender",
]

# Minimum thresholds
MIN_VALID_ROWS = 600                     # At least 600 rows after cleaning
MIN_MONTHS_PER_USER = 6                  # At least 6 distinct months per user

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def load_config() -> Dict[str, Any]:
    """
    Load configuration for data paths and Zenodo DOI.

    Returns
    -------
    dict
        Mapping with keys:
        - zenodo_doi: str, DOI of the dataset
        - output_path: Path, where the final Parquet should be stored
        - checksum_path: Path, where the checksum file should be stored
    """
    try:
        cfg = get_config()
        return {
            "zenodo_doi": cfg.get("data", {}).get(
                "zenodo_loneliness_doi",
                "10.5281/zenodo.1234567"  # Default placeholder DOI
            ),
            "output_path": Path(
                cfg.get("paths", {}).get(
                    "raw_loneliness_dataset",
                    "data/raw/loneliness_dataset.parquet"
                )
            ),
            "checksum_path": Path(
                cfg.get("paths", {}).get(
                    "raw_checksum",
                    "data/raw/loneliness_dataset.sha256"
                )
            ),
        }
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def _extract_record_id_from_doi(doi: str) -> str:
    """
    Zenodo DOIs are of the form ``10.5281/zenodo.<record_id>``.
    This helper extracts the numeric record ID.
    """
    try:
        return doi.split(".")[-1]
    except Exception as e:
        raise ValueError(f"Unable to parse record ID from DOI '{doi}': {e}")


def fetch_dataset(zenodo_doi: str, download_dir: Path) -> Path:
    """
    Download the dataset from Zenodo using the ``zenodo_get`` utility.

    Parameters
    ----------
    zenodo_doi : str
        The DOI of the dataset.
    download_dir : pathlib.Path
        Directory to save the downloaded file.

    Returns
    -------
    pathlib.Path
        Path to the primary data file (CSV or Parquet).

    Raises
    ------
    RuntimeError
        If the download fails or no suitable data file is found.
    """
    logger.info(f"Fetching dataset from Zenodo DOI: {zenodo_doi}")
    download_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ``zenodo_get`` expects an iterable of DOIs.
        # It returns a list of downloaded file paths.
        downloaded_paths = _zenodo_get.zenodo_get([zenodo_doi], output_dir=str(download_dir))
    except Exception as e:
        logger.error(f"zenodo_get failed: {e}")
        raise RuntimeError(f"Failed to download dataset via zenodo_get: {e}")

    if not downloaded_paths:
        raise RuntimeError(f"zenodo_get returned no files for DOI {zenodo_doi}")

    # Choose the first file that looks like a data file.
    for path_str in downloaded_paths:
        p = Path(path_str)
        if p.suffix.lower() in {".csv", ".parquet"}:
            logger.info(f"Selected data file: {p}")
            return p
    
    # If we get here, no appropriate file was found.
    raise RuntimeError(f"No CSV or Parquet file found among downloaded artifacts: {downloaded_paths}")


def load_dataframe(file_path: Path) -> pd.DataFrame:
    """
    Load a CSV or Parquet file into a pandas DataFrame.

    Parameters
    ----------
    file_path : pathlib.Path

    Returns
    -------
    pandas.DataFrame
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_path.suffix}")

    logger.info(f"Loaded {len(df)} rows from {file_path.name}")
    return df


def validate_columns(df: pd.DataFrame) -> None:
    """
    Ensure the DataFrame contains all required columns.

    Raises
    ------
    ValueError
        If any required column is missing.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    logger.info("All required columns are present.")


def enforce_longitudinal_depth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only users that have at least ``MIN_MONTHS_PER_USER`` distinct
    calendar months with a non‑null UCLA Loneliness score.

    Returns
    -------
    pandas.DataFrame
        Filtered DataFrame.
    """
    # Ensure timestamp column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Drop rows where the score or timestamp is null (cannot be used for depth)
    df_valid = df.dropna(subset=["UCLA_Loneliness_Score", "timestamp"])

    # Extract year‑month identifier
    df_valid["year_month"] = df_valid["timestamp"].dt.to_period("M")

    # Count distinct months per user
    month_counts = (
        df_valid.groupby("username_hash")["year_month"]
        .nunique()
        .reset_index(name="month_count")
    )

    eligible_users = month_counts[month_counts["month_count"] >= MIN_MONTHS_PER_USER][
        "username_hash"
    ]

    filtered_df = df[df["username_hash"].isin(eligible_users)].copy()
    logger.info(
        f"Longitudinal depth filter: {len(eligible_users)} users retained "
        f"out of {df['username_hash'].nunique()} total."
    )
    return filtered_df


def final_row_count_check(df: pd.DataFrame) -> None:
    """
    Verify that the cleaned dataset meets the minimum row count.

    Raises
    ------
    ValueError
        If the row count is below ``MIN_VALID_ROWS``.
    """
    row_count = len(df)
    if row_count < MIN_VALID_ROWS:
        raise ValueError(
            f"Dataset contains only {row_count} rows after filtering; "
            f"minimum required is {MIN_VALID_ROWS}."
        )
    logger.info(f"Row count check passed ({row_count} rows).")


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------

def main() -> None:
    """Orchestrates the download, validation, filtering, and persistence of the dataset."""
    log_stage_start("T003: Download Reddit Loneliness Longitudinal Dataset")

    try:
        cfg = load_config()
        output_path: Path = Path(cfg["output_path"])
        checksum_path: Path = Path(cfg["checksum_path"])

        # -----------------------------------------------------------------
        # Step 1 – Download
        # -----------------------------------------------------------------
        raw_file = fetch_dataset(cfg["zenodo_doi"], Path("data/raw"))

        # -----------------------------------------------------------------
        # Step 2 – Load into DataFrame
        # -----------------------------------------------------------------
        df = load_dataframe(raw_file)

        # -----------------------------------------------------------------
        # Step 3 – Validate column schema
        # -----------------------------------------------------------------
        validate_columns(df)

        # -----------------------------------------------------------------
        # Step 4 – Enforce longitudinal depth (≥6 months per user)
        # -----------------------------------------------------------------
        df = enforce_longitudinal_depth(df)

        # -----------------------------------------------------------------
        # Step 5 – Minimum row count check (≥600 rows)
        # -----------------------------------------------------------------
        final_row_count_check(df)

        # -----------------------------------------------------------------
        # Step 6 – Persist cleaned dataset as Parquet and record checksum
        # -----------------------------------------------------------------
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        logger.info(f"Cleaned dataset written to {output_path}")

        # Record checksum for provenance
        record_checksum(output_path, checksum_path)
        logger.info(f"Checksum recorded at {checksum_path}")

        log_stage_end("T003: Download Reddit Loneliness Longitudinal Dataset", success=True)

    except Exception as exc:
        log_error_context("T003: Download Reddit Loneliness Longitudinal Dataset - Failed", exc)
        log_stage_end("T003: Download Reddit Loneliness Longitudinal Dataset", success=False)
        # Re‑raise so that the orchestrator (`src/main.py`) exits with a non‑zero code.
        raise


if __name__ == "__main__":
    main()
