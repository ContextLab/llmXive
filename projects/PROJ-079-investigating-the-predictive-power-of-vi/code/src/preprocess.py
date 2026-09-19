import logging
import csv
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path
import pandas as pd

from src.config import DATA_PROCESSED_PATH
from src.utils.logging import get_logger

logger = get_logger(__name__)

def filter_samples(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the merged dataset to remove rows with missing strain links
    and ensure a minimum sample count.

    This function enforces FR-013 (minimum 30 samples) and FR-014 (valid strain links).

    Parameters
    ----------
    merged_df : pd.DataFrame
        The merged dataset containing viral features and host expression scores.
        Must contain a 'strain_accession' column.

    Returns
    -------
    pd.DataFrame
        The filtered DataFrame containing only valid samples.

    Raises
    ------
    ValueError
        If the filtered dataset contains fewer than 30 samples.
    """
    logger.info("Starting sample filtering process...")

    if merged_df.empty:
        logger.error("Input DataFrame is empty. Cannot filter samples.")
        raise ValueError("Input DataFrame is empty.")

    if 'strain_accession' not in merged_df.columns:
        logger.error("Input DataFrame missing required 'strain_accession' column.")
        raise ValueError("Input DataFrame must contain 'strain_accession' column.")

    # Count total rows before filtering
    total_rows_before = len(merged_df)
    logger.info(f"Total rows before filtering: {total_rows_before}")

    # Remove rows with missing strain links (NaN, None, or empty strings)
    valid_mask = merged_df['strain_accession'].notna()
    # Also handle empty strings if any
    valid_mask = valid_mask & (merged_df['strain_accession'].astype(str).str.strip() != '')

    filtered_df = merged_df[valid_mask].copy()
    rows_removed = total_rows_before - len(filtered_df)

    if rows_removed > 0:
        logger.warning(f"Removed {rows_removed} rows due to missing/invalid strain links.")
    else:
        logger.info("No rows removed due to missing strain links.")

    # Check minimum sample count constraint (FR-013)
    min_samples = 30
    if len(filtered_df) < min_samples:
        error_msg = (
            f"Filtered dataset has {len(filtered_df)} samples, which is below "
            f"the required minimum of {min_samples} (FR-013). Pipeline aborted."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Sample filtering complete. {len(filtered_df)} valid samples remain.")
    return filtered_df

def save_filtered_samples(filtered_df: pd.DataFrame, output_path: Optional[str] = None) -> Path:
    """
    Save the filtered dataset to a CSV file.

    Parameters
    ----------
    filtered_df : pd.DataFrame
        The filtered DataFrame to save.
    output_path : str, optional
        Path to save the CSV file. If None, uses default path in data/processed/.

    Returns
    -------
    Path
        Path to the saved file.
    """
    if output_path is None:
        output_path = str(Path(DATA_PROCESSED_PATH) / "filtered_dataset.csv")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered dataset saved to {output_path}")
    return output_path

def run_filter_pipeline(merged_df: pd.DataFrame, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Run the complete filtering pipeline: filter samples and save results.

    Parameters
    ----------
    merged_df : pd.DataFrame
        The input merged dataset.
    output_path : str, optional
        Path to save the filtered dataset.

    Returns
    -------
    pd.DataFrame
        The filtered DataFrame.
    """
    logger.info("Running filter pipeline...")
    filtered_df = filter_samples(merged_df)
    save_filtered_samples(filtered_df, output_path)
    return filtered_df