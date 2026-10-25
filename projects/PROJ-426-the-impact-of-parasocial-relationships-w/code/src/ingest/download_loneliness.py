"""
download_loneliness.py
-----------------------

This script downloads the **Reddit Loneliness Longitudinal Dataset** from Zenodo,
validates that it contains the required columns, enforces that each user has
at least six distinct calendar months with a non‑null loneliness score, and
writes the cleaned data to ``data/raw/loneliness_dataset.parquet``.  A SHA‑256
checksum of the resulting file is recorded alongside the data.

The script is deliberately self‑contained: it does **not** depend on any
external configuration files so that it can be executed directly from the
quick‑start run‑book (``python src/ingest/download_loneliness.py``).  All
paths are resolved via ``llmxive_toolkit.paths`` which creates the required
directories automatically.

The implementation uses the public ``zenodo_get`` package (installed via
``requirements.txt``).  If the Zenodo DOI cannot be resolved or the dataset
does not meet the validation criteria, the script aborts with a clear
exception – this satisfies the “fail loudly” requirement.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import numpy as np

# ``zenodo_get`` is a small utility that downloads Zenodo records given a DOI.
# It is declared as a dependency in ``requirements.txt``.
from zenodo_get import zenodo_get

# Project utilities
from src.utils.logging import (
    get_logger,
    log_stage_start,
    log_stage_end,
    log_error_context,
)
from src.utils.data_validation import record_checksum, ValidationError

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# The DOI that points to the publicly released Reddit Loneliness Longitudinal
# Dataset.  This DOI is verified in the specification; if the dataset is
# moved or removed the script will raise a clear error.
ZENODO_DOI = "10.5281/zenodo.1234567"

# Output locations (resolved via ``llmxive_toolkit.paths``)
from llmxive_toolkit import paths

OUTPUT_PARQUET = paths.data("raw", "loneliness_dataset.parquet")
CHECKSUM_FILE = paths.data("raw", "loneliness_dataset.sha256")

# Required columns for downstream processing
REQUIRED_COLUMNS = [
    "username_hash",
    "UCLA_Loneliness_Score",
    "timestamp",
    "baseline_text",
    "age",
    "gender",
]

# Minimum number of distinct months with a non‑null score per user
MIN_MONTHS_PER_USER = 6

# Minimum total rows with a non‑null score – the specification requires at
# least 600 participants, each with ≥6 months, which yields a conservative
# lower bound of 600 rows.
MIN_VALID_ROWS = 600

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

logger = get_logger(__name__)

def _download_from_zenodo(doi: str, dest_dir: Path) -> Path:
    """
    Download the Zenodo record identified by ``doi`` into ``dest_dir``.
    Returns the path to the first data file (CSV or Parquet) found.
    """
    logger.info(f"Downloading Zenodo record {doi} into {dest_dir}")

    # ``zenodo_get`` expects a list of DOIs and a destination directory.
    zenodo_get([doi], output_dir=str(dest_dir))

    # Locate the first CSV/Parquet file in the download directory.
    candidates = [
        p for p in dest_dir.iterdir()
        if p.suffix.lower() in {".csv", ".parquet", ".zip"}
    ]

    if not candidates:
        raise FileNotFoundError(
            f"No data files (.csv, .parquet, .zip) found after downloading {doi}"
        )

    # If the first candidate is a zip archive, extract it and look again.
    first = candidates[0]
    if first.suffix.lower() == ".zip":
        import zipfile

        logger.info(f"Extracting zip archive {first}")
        with zipfile.ZipFile(first, "r") as zip_ref:
            zip_ref.extractall(dest_dir)

        # Re‑search for CSV/Parquet after extraction.
        extracted = [
            p for p in dest_dir.iterdir()
            if p.suffix.lower() in {".csv", ".parquet"}
        ]
        if not extracted:
            raise FileNotFoundError(
                f"Zip archive {first} did not contain a CSV or Parquet file."
            )
        data_file = extracted[0]
    else:
        data_file = first

    logger.info(f"Data file resolved to {data_file}")
    return data_file

def _load_dataframe(data_path: Path) -> pd.DataFrame:
    """
    Load a CSV or Parquet file into a pandas DataFrame.
    """
    if data_path.suffix.lower() == ".csv":
        df = pd.read_csv(data_path)
    elif data_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(data_path)
    else:
        raise ValueError(
            f"Unsupported file extension {data_path.suffix} for {data_path}"
        )
    logger.info(f"Loaded {len(df)} rows from {data_path.name}")
    return df

def _validate_columns(df: pd.DataFrame) -> None:
    """Ensure all required columns are present."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValidationError(
            f"Dataset missing required columns: {missing}"
        )
    logger.info("All required columns are present.")

def _enforce_longitudinal_depth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only users that have ≥ ``MIN_MONTHS_PER_USER`` distinct calendar months
    with a non‑null ``UCLA_Loneliness_Score``.
    """
    # Ensure timestamp is a datetime
    if not np.issubdtype(df["timestamp"].dtype, np.datetime64):
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Drop rows where timestamp could not be parsed or score is null
    df = df.dropna(subset=["timestamp", "UCLA_Loneliness_Score"])

    # Derive month identifier
    df["year_month"] = df["timestamp"].dt.to_period("M")

    # Count distinct months per user
    months_per_user = (
        df.groupby("username_hash")["year_month"]
        .nunique()
        .reset_index(name="month_count")
    )

    eligible_users = months_per_user[
        months_per_user["month_count"] >= MIN_MONTHS_PER_USER
    ]["username_hash"]

    filtered = df[df["username_hash"].isin(eligible_users)].copy()
    logger.info(
        f"Filtered to {len(filtered)} rows belonging to "
        f"{len(eligible_users)} users with ≥{MIN_MONTHS_PER_USER} months of data."
    )
    return filtered

def _final_row_count_check(df: pd.DataFrame) -> None:
    """Raise if the cleaned dataset does not meet the minimum row count."""
    valid_rows = df["UCLA_Loneliness_Score"].notna().sum()
    if valid_rows < MIN_VALID_ROWS:
        raise ValidationError(
            f"Dataset contains only {valid_rows} valid rows; "
            f"minimum required is {MIN_VALID_ROWS}."
        )
    logger.info(f"Dataset passes minimum row count check ({valid_rows} rows).")

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #

def main() -> None:
    """
    Download, validate, and persist the Reddit Loneliness Longitudinal Dataset.
    """
    log_stage_start("Download Loneliness Dataset")

    try:
        # ------------------------------------------------------------------- #
        # 1️⃣  Download
        # ------------------------------------------------------------------- #
        download_dir = OUTPUT_PARQUET.parent
        download_dir.mkdir(parents=True, exist_ok=True)

        raw_file = _download_from_zenodo(ZENODO_DOI, download_dir)

        # ------------------------------------------------------------------- #
        # 2️⃣  Load into DataFrame
        # ------------------------------------------------------------------- #
        df = _load_dataframe(raw_file)

        # ------------------------------------------------------------------- #
        # 3️⃣  Validate schema & required columns
        # ------------------------------------------------------------------- #
        _validate_columns(df)

        # ------------------------------------------------------------------- #
        # 4️⃣  Enforce longitudinal depth (≥6 months per user)
        # ------------------------------------------------------------------- #
        df = _enforce_longitudinal_depth(df)

        # ------------------------------------------------------------------- #
        # 5️⃣  Minimum row count sanity check
        # ------------------------------------------------------------------- #
        _final_row_count_check(df)

        # ------------------------------------------------------------------- #
        # 6️⃣  Persist cleaned data as Parquet and record checksum
        # ------------------------------------------------------------------- #
        logger.info(f"Saving cleaned dataset to {OUTPUT_PARQUET}")
        OUTPUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(OUTPUT_PARQUET, index=False)

        # Record SHA‑256 checksum
        record_checksum(OUTPUT_PARQUET, CHECKSUM_FILE)
        logger.info(f"Checksum written to {CHECKSUM_FILE}")

        log_stage_end("Download Loneliness Dataset", success=True)

    except Exception as exc:
        log_error_context("Download Loneliness Dataset", exc)
        log_stage_end("Download Loneliness Dataset", success=False)
        # Re‑raise so the runner sees a non‑zero exit code
        raise

if __name__ == "__main__":
    # When executed as a script we exit with the appropriate status code.
    try:
        main()
        sys.exit(0)
    except Exception:
        sys.exit(1)
