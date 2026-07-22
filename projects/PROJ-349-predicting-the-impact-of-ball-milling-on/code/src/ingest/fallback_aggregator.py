"""
Fallback Aggregator for Ball Milling Dataset (T013c).

This module implements the fallback aggregation logic:
If the total count of aggregated rows from T012, T013, and T013b is < 150,
it loads the pre-verified, static subset from `data/fallback/verified_static_subset.csv`
to reach the minimum viable threshold.

Constraint: This is a REAL dataset subset, not synthetic generation.
"""

import logging
import os
import pandas as pd
from pathlib import Path
from typing import Optional

from src.exceptions import DataIngestionError, InsufficientDataError

logger = logging.getLogger(__name__)

FALLBACK_PATH = Path("data/fallback/verified_static_subset.csv")
MIN_ROWS = 150
TARGET_ROWS = 500

def load_fallback_data() -> pd.DataFrame:
    """
    Load the pre-verified static fallback dataset.

    Returns:
        pd.DataFrame: The fallback dataset.

    Raises:
        DataIngestionError: If the fallback file does not exist or is empty.
        InsufficientDataError: If the fallback dataset has fewer than 150 rows.
    """
    if not FALLBACK_PATH.exists():
        raise DataIngestionError(
            f"Fallback file not found at {FALLBACK_PATH}. "
            "Ensure T013d has completed successfully."
        )

    try:
        df = pd.read_csv(FALLBACK_PATH)
    except Exception as e:
        raise DataIngestionError(f"Failed to load fallback data: {e}") from e

    if df.empty:
        raise DataIngestionError(
            f"Fallback file {FALLBACK_PATH} is empty. "
            "It must contain at least 150 rows of real data."
        )

    if len(df) < MIN_ROWS:
        raise InsufficientDataError(
            f"Fallback dataset has {len(df)} rows, but minimum viable threshold is {MIN_ROWS}. "
            "T013d must provide a verified subset of at least 150 rows."
        )

    logger.info(f"Loaded fallback dataset with {len(df)} rows from {FALLBACK_PATH}")
    return df

def append_fallback_if_needed(
    current_df: pd.DataFrame,
    fallback_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Append fallback data if the current dataset count is below the minimum viable threshold.

    Args:
        current_df: The current merged dataset from T012, T013, T013b.
        fallback_df: Optional pre-loaded fallback DataFrame. If None, loads from disk.

    Returns:
        pd.DataFrame: The updated dataset (either original or with fallback appended).
    """
    current_count = len(current_df)

    if current_count >= MIN_ROWS:
        logger.info(
            f"Current dataset has {current_count} rows (>= {MIN_ROWS}). "
            "No fallback needed."
        )
        return current_df

    logger.warning(
        f"Current dataset has {current_count} rows (< {MIN_ROWS}). "
        "Attempting to load and append fallback data."
    )

    if fallback_df is None:
        fallback_df = load_fallback_data()

    # Check if we have enough data after appending
    new_count = current_count + len(fallback_df)
    if new_count < MIN_ROWS:
        raise InsufficientDataError(
            f"After appending fallback, total rows = {new_count}, "
            "which is still below the minimum viable threshold of {MIN_ROWS}. "
            "The fallback dataset itself may be insufficient."
        )

    # Append fallback data
    # Ensure columns align (fallback should have same schema as current)
    # We select only columns present in current_df to avoid mismatches if fallback has extras
    common_cols = [col for col in fallback_df.columns if col in current_df.columns]
    
    if not common_cols:
        raise DataIngestionError(
            "No common columns found between current dataset and fallback dataset. "
            "Schema mismatch detected."
        )

    fallback_subset = fallback_df[common_cols]
    result_df = pd.concat([current_df, fallback_subset], ignore_index=True)

    logger.info(
        f"Appended {len(fallback_subset)} fallback rows. "
        f"New total: {len(result_df)} rows."
    )

    return result_df

def run_fallback_aggregation(
    current_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main entry point for fallback aggregation logic.

    Args:
        current_df: The current merged dataset.
        output_path: Optional path to write the result. If None, only returns the DataFrame.

    Returns:
        pd.DataFrame: The aggregated dataset meeting the minimum threshold.
    """
    result_df = append_fallback_if_needed(current_df)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_parquet(output_path, index=False)
        logger.info(f"Wrote aggregated dataset to {output_path}")

    return result_df
