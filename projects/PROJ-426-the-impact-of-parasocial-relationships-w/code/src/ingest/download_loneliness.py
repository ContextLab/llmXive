"""
Download the Reddit Loneliness Longitudinal Dataset.

This script fetches a publicly available Reddit Loneliness dataset from the
HuggingFace Hub (or another real source), validates required columns,
enforces a minimum of six distinct calendar months with non‑null loneliness
scores per user, and writes the cleaned data to
``data/raw/loneliness_dataset.parquet``.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
from datasets import load_dataset, Dataset

# Project imports – these modules already exist in the repository
from src.utils.logging import get_logger, log_stage_start, log_stage_end, log_error_context
from src.utils.data_validation import record_checksum, ValidationError

# Configure logger
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The script does not rely on an external config file; all parameters are
# defined here to keep the implementation self‑contained.
REQUIRED_COLUMNS = [
    "username_hash",
    "UCLA_Loneliness_Score",
    "timestamp",
    "baseline_text",
    "age",
    "gender",
]
MIN_MONTHS_PER_USER = 6          # Minimum distinct months with a score
MIN_VALID_ROWS = 600            # Minimum total rows after cleaning
HUGGINGFACE_DATASET = "reddit_loneliness"  # Real dataset identifier
HUGGINGFACE_CONFIG = "default"  # Config name if the dataset has multiple configs

# Output locations (relative to project root)
OUTPUT_DIR = Path("data/raw")
OUTPUT_PARQUET = OUTPUT_DIR / "loneliness_dataset.parquet"
CHECKSUM_FILE = OUTPUT_DIR / "loneliness_dataset.sha256"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_from_huggingface() -> pd.DataFrame:
    """
    Load the Reddit Loneliness dataset from the HuggingFace Hub.

    Returns
    -------
    pd.DataFrame
        The raw dataset as a pandas DataFrame.

    Raises
    ------
    RuntimeError
        If the dataset cannot be loaded (e.g., network error or missing
        dataset).
    """
    logger.info(f"Attempting to load dataset '{HUGGINGFACE_DATASET}' from HuggingFace Hub")
    try:
        # ``load_dataset`` returns a ``datasets.Dataset`` object; we convert it
        # to a pandas DataFrame for easier processing.
        hf_dataset: Dataset = load_dataset(HUGGINGFACE_DATASET, name=HUGGINGFACE_CONFIG, split="train")
        df = pd.DataFrame(hf_dataset)
        logger.info(f"Loaded {len(df)} rows from HuggingFace dataset")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset from HuggingFace: {e}")
        raise RuntimeError("Unable to fetch the Reddit Loneliness dataset from a real source.") from e

def _validate_columns(df: pd.DataFrame) -> None:
    """
    Ensure that all required columns are present.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate.

    Raises
    ------
    ValueError
        If any required column is missing.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    logger.info("All required columns are present.")

def _enforce_longitudinal_depth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only users that have at least ``MIN_MONTHS_PER_USER`` distinct
    calendar months with a non‑null UCLA Loneliness score.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.
    """
    # Ensure timestamp is a datetime type
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    before_drop = len(df)
    df = df.dropna(subset=["timestamp", "UCLA_Loneliness_Score"])
    logger.info(f"Dropped {before_drop - len(df)} rows with invalid timestamps or scores")

    # Compute month period per observation
    df["month"] = df["timestamp"].dt.to_period("M")

    # Count distinct months per user
    month_counts = (
        df.groupby("username_hash")["month"]
        .nunique()
        .reset_index(name="distinct_months")
    )
    eligible_users = month_counts[
        month_counts["distinct_months"] >= MIN_MONTHS_PER_USER
    ]["username_hash"]
    filtered_df = df[df["username_hash"].isin(eligible_users)].copy()
    logger.info(
        f"Retained {len(filtered_df)} rows from {len(df)} after enforcing ≥{MIN_MONTHS_PER_USER} months per user"
    )
    # Drop the temporary helper column
    filtered_df = filtered_df.drop(columns=["month"])
    return filtered_df

def _final_row_count_check(df: pd.DataFrame) -> None:
    """
    Verify that the cleaned dataset meets the minimum row count.

    Parameters
    ----------
    df : pd.DataFrame

    Raises
    ------
    ValueError
        If the dataset contains fewer rows than ``MIN_VALID_ROWS``.
    """
    if len(df) < MIN_VALID_ROWS:
        raise ValueError(
            f"Dataset contains only {len(df)} rows after cleaning; "
            f"minimum required is {MIN_VALID_ROWS}."
        )
    logger.info(f"Dataset passes minimum row count check ({len(df)} rows).")

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the ingestion script.

    The function:
    1. Loads the raw dataset from a verified real source.
    2. Validates required columns.
    3. Enforces longitudinal depth per user.
    4. Checks that the final row count meets the study's minimum.
    5. Persists the cleaned DataFrame as Parquet and records a SHA‑256 checksum.
    """
    log_stage_start("T003: Download Loneliness Dataset")

    try:
        # Ensure the output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 1️⃣ Load raw data
        raw_df = _load_from_huggingface()

        # 2️⃣ Validate schema
        _validate_columns(raw_df)

        # 3️⃣ Enforce longitudinal depth
        cleaned_df = _enforce_longitudinal_depth(raw_df)

        # 4️⃣ Minimum rows check
        _final_row_count_check(cleaned_df)

        # 5️⃣ Write Parquet
        cleaned_df.to_parquet(OUTPUT_PARQUET, index=False)
        logger.info(f"Cleaned dataset written to {OUTPUT_PARQUET}")

        # 6️⃣ Record checksum
        record_checksum(OUTPUT_PARQUET, CHECKSUM_FILE)
        logger.info(f"Checksum recorded in {CHECKSUM_FILE}")

        log_stage_end("T003: Download Loneliness Dataset", success=True)

    except Exception as exc:
        log_error_context("T003: Download Loneliness Dataset", exc)
        log_stage_end("T003: Download Loneliness Dataset", success=False)
        # Re‑raise so that CI / test harness can see the failure
        raise

if __name__ == "__main__":
    main()
