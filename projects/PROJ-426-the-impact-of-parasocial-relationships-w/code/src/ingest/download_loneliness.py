"""
Download the Reddit Loneliness Longitudinal Dataset from Zenodo.

This script fetches the dataset associated with the DOI provided in the
configuration, validates that all required columns are present, enforces
a minimum longitudinal depth (≥ 6 distinct calendar months with a
non‑null UCLA Loneliness score per user), checks that the cleaned dataset
contains at least 600 rows, and writes the result as Parquet together with
a SHA‑256 checksum.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import hashlib
import zipfile

# Ensure project root is on sys.path when the script is executed directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from zenodo_get import zenodo_get
from src.utils.logging import get_logger, log_stage_start, log_stage_end, log_error_context
from src.utils.config import get_config
from src.utils.data_validation import record_checksum, ValidationError

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "username_hash",
    "UCLA_Loneliness_Score",
    "timestamp",
    "baseline_text",
    "age",
    "gender",
]

MIN_MONTHS_PER_USER = 6          # longitudinal depth requirement
MIN_VALID_ROWS = 600            # overall row count requirement

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
    cfg = get_config()
    return {
        "zenodo_doi": cfg.get("data", {}).get(
            "zenodo_loneliness_doi", "10.5281/zenodo.123456"
        ),
        "output_path": Path(
            cfg.get("paths", {})
            .get("raw_loneliness_dataset", "data/raw/loneliness_dataset.parquet")
        ),
        "checksum_path": Path(
            cfg.get("paths", {})
            .get("raw_loneliness_checksum", "data/raw/loneliness_dataset.sha256")
        ),
    }

def fetch_dataset(doi: str, download_dir: Path) -> Path:
    """
    Download the dataset from Zenodo using the ``zenodo_get`` utility.

    Parameters
    ----------
    doi : str
        Zenodo DOI.
    download_dir : pathlib.Path
        Directory where the files should be placed.

    Returns
    -------
    pathlib.Path
        Path to the primary data file (CSV, Parquet, or extracted file).

    Raises
    ------
    RuntimeError
        If the download fails or no suitable data file is found.
    """
    logger.info(f"Downloading Zenodo dataset DOI: {doi}")
    try:
        zenodo_get([doi], output_dir=str(download_dir))
    except Exception as exc:
        logger.error(f"zenodo_get failed: {exc}")
        raise RuntimeError(f"Failed to download dataset from Zenodo DOI {doi}") from exc

    # Find a data file (CSV, Parquet, or ZIP containing one of those)
    candidates = list(download_dir.rglob("*"))
    data_file = None
    for candidate in candidates:
        if candidate.suffix.lower() in {".csv", ".parquet"}:
            data_file = candidate
            break
        if candidate.suffix.lower() == ".zip":
            # Extract ZIP to a temporary location inside download_dir
            with zipfile.ZipFile(candidate, "r") as zf:
                zf.extractall(download_dir)
            # After extraction, look again for CSV/Parquet
            for extracted in download_dir.rglob("*"):
                if extracted.suffix.lower() in {".csv", ".parquet"}:
                    data_file = extracted
                    break
        if data_file:
            break

    if data_file is None:
        raise RuntimeError(
            f"No CSV/Parquet data file found after downloading DOI {doi}"
        )
    logger.info(f"Dataset file resolved to: {data_file}")
    return data_file

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
    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_path.suffix}")
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
        raise ValueError(
            f"Dataset missing required columns: {missing}"
        )
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
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Drop rows with missing timestamp or score
    df = df.dropna(subset=["timestamp", "UCLA_Loneliness_Score"])

    # Create month identifier
    df["year_month"] = df["timestamp"].dt.to_period("M")

    # Count distinct months per user
    month_counts = (
        df.groupby("username_hash")["year_month"]
        .nunique()
        .reset_index(name="month_count")
    )

    eligible_users = month_counts[
        month_counts["month_count"] >= MIN_MONTHS_PER_USER
    ]["username_hash"]

    filtered = df[df["username_hash"].isin(eligible_users)].copy()
    filtered.drop(columns=["year_month"], inplace=True)

    logger.info(
        f"Longitudinal depth filter: {len(eligible_users)} users retained "
        f"out of {df['username_hash'].nunique()} total."
    )
    return filtered

def final_row_count_check(df: pd.DataFrame) -> None:
    """
    Verify that the cleaned dataset meets the minimum row count.

    Raises
    ------
    ValueError
        If the row count is below ``MIN_VALID_ROWS``.
    """
    if len(df) < MIN_VALID_ROWS:
        raise ValueError(
            f"Dataset contains only {len(df)} rows after cleaning; "
            f"minimum required is {MIN_VALID_ROWS}."
        )
    logger.info(f"Row count check passed ({len(df)} rows).")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the download, validation, filtering, and persistence of
    the Reddit Loneliness Longitudinal Dataset.
    """
    log_stage_start("T003: Download Loneliness Dataset")
    try:
        cfg = load_config()
        output_path: Path = cfg["output_path"]
        checksum_path: Path = cfg["checksum_path"]
        download_dir = Path("data/raw")
        download_dir.mkdir(parents=True, exist_ok=True)

        # ------------------------------------------------------------------
        # 1. Download
        # ------------------------------------------------------------------
        raw_file = fetch_dataset(cfg["zenodo_doi"], download_dir)

        # ------------------------------------------------------------------
        # 2. Load into DataFrame
        # ------------------------------------------------------------------
        df = load_dataframe(raw_file)

        # ------------------------------------------------------------------
        # 3. Validate required columns
        # ------------------------------------------------------------------
        validate_columns(df)

        # ------------------------------------------------------------------
        # 4. Enforce longitudinal depth (≥6 months per user)
        # ------------------------------------------------------------------
        df = enforce_longitudinal_depth(df)

        # ------------------------------------------------------------------
        # 5. Final row count verification (≥600 rows)
        # ------------------------------------------------------------------
        final_row_count_check(df)

        # ------------------------------------------------------------------
        # 6. Persist cleaned data as Parquet and write checksum
        # ------------------------------------------------------------------
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        logger.info(f"Cleaned dataset written to {output_path}")

        # Record checksum
        record_checksum(output_path, checksum_path)
        logger.info(f"Checksum written to {checksum_path}")

        log_stage_end("T003: Download Loneliness Dataset - Success")
    except Exception as exc:
        log_error_context("T003: Download Loneliness Dataset - Failed", exc)
        raise

if __name__ == "__main__":
    main()
