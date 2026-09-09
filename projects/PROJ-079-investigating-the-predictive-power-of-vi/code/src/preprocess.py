import logging
import csv
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path
import pandas as pd
import sys

from src.config import DATA_PROCESSED_PATH, SEED
from src.utils.logging import get_logger

logger = get_logger(__name__)

def filter_samples(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows with missing strain links and ensures >=30 samples remain.
    Aborts the pipeline with a fatal error if fewer than 30 samples remain.

    Per FR-013: Pipeline MUST abort if N < 30.

    Args:
        merged_df: DataFrame containing the merged dataset with at least
                   a 'strain_accession' column.

    Returns:
        Filtered DataFrame with valid strain links and >= 30 rows.

    Raises:
        SystemExit: If the number of valid samples is less than 30.
    """
    if merged_df.empty:
        logger.error("Input DataFrame is empty. Cannot filter samples.")
        sys.exit(1)

    # Identify the column name for strain linkage.
    # The schema expects 'strain_accession' based on T012/T013/T021 specs.
    strain_col = 'strain_accession'
    
    if strain_col not in merged_df.columns:
        logger.error(f"Required column '{strain_col}' not found in merged DataFrame. "
                     f"Available columns: {list(merged_df.columns)}")
        sys.exit(1)

    logger.info(f"Starting sample filtering. Total rows: {len(merged_df)}")

    # Remove rows where strain_accession is missing (NaN, None, or empty string)
    initial_count = len(merged_df)
    filtered_df = merged_df.dropna(subset=[strain_col])
    
    # Also drop rows where strain_accession is an empty string if it exists
    if not filtered_df.empty:
        filtered_df = filtered_df[filtered_df[strain_col].astype(str).str.strip() != ""]
    
    final_count = len(filtered_df)
    removed_count = initial_count - final_count

    if removed_count > 0:
        logger.warning(f"Removed {removed_count} rows due to missing/empty '{strain_col}'.")
    else:
        logger.info("No rows removed due to missing strain links.")

    # Enforce minimum sample size per FR-013
    MIN_SAMPLES = 30
    if final_count < MIN_SAMPLES:
        error_msg = (
            f"CRITICAL: After filtering, only {final_count} samples remain. "
            f"Minimum required is {MIN_SAMPLES} per FR-013. "
            f"Aborting pipeline."
        )
        logger.critical(error_msg)
        # Raise SystemExit with non-zero code to abort the pipeline
        sys.exit(1)

    logger.info(f"Filtering complete. Remaining samples: {final_count} (>= {MIN_SAMPLES}).")
    return filtered_df

def save_filtered_samples(filtered_df: pd.DataFrame, output_path: Optional[str] = None) -> Path:
    """
    Saves the filtered DataFrame to a CSV file.
    
    Args:
        filtered_df: The filtered DataFrame.
        output_path: Optional path to save the file. Defaults to 
                     'data/processed/filtered_dataset.csv'.
                     
    Returns:
        Path object of the saved file.
    """
    if output_path is None:
        output_path = str(Path(DATA_PROCESSED_PATH) / "filtered_dataset.csv")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    filtered_df.to_csv(output_file, index=False)
    logger.info(f"Filtered dataset saved to {output_file}")
    return output_file
