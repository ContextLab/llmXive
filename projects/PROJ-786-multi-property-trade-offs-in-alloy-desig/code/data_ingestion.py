"""
Data Ingestion Module for Alloy Design Project.

Fetches OQMD elastic properties data via HuggingFace, filters for valid
Bulk and Shear Moduli entries, and prepares the dataset for downstream
processing. Implements the pivot to DFT proxies as per FR-001.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
import pandas as pd

# Add project root to path for imports if running as script
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from datasets import load_dataset
from config import get_config, verify_config
from utils.logging_config import get_logger, log_info_with_context, log_error_with_context, log_warning_with_context

# Initialize logger for this module
logger = get_logger(__name__)

def load_oqmd_data(dataset_name: str = "OQMD/elastic_properties", 
                   streaming: bool = False) -> Optional[pd.DataFrame]:
    """
    Fetches the OQMD elastic properties dataset from HuggingFace.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        streaming: If True, streams the dataset (useful for large datasets).

    Returns:
        A pandas DataFrame containing the dataset, or None if loading fails.
    """
    try:
        log_info_with_context(logger, f"Loading dataset: {dataset_name}")
        dataset = load_dataset(dataset_name, split="train", streaming=streaming)
        
        # Convert to DataFrame
        if streaming:
            df = pd.DataFrame(dataset)
        else:
            df = dataset.to_pandas()
        
        log_info_with_context(logger, f"Dataset loaded successfully. Shape: {df.shape}")
        return df
    except Exception as e:
        log_error_with_context(logger, f"Failed to load dataset {dataset_name}: {str(e)}")
        return None

def filter_valid_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the dataframe for entries with valid Bulk and Shear Moduli.
    
    Implements FR-001: Filter for entries with `bulk_modulus` and `shear_modulus` > 0
    and exclude missing data.

    Args:
        df: The raw dataframe from OQMD.

    Returns:
        Filtered dataframe containing only valid entries.
    """
    if df is None or df.empty:
        log_warning_with_context(logger, "Input dataframe is empty or None")
        return pd.DataFrame()

    required_columns = ["bulk_modulus", "shear_modulus"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        log_error_with_context(logger, f"Missing required columns: {missing_cols}")
        return pd.DataFrame()

    initial_count = len(df)
    log_info_with_context(logger, f"Starting filter on {initial_count} rows")

    # Filter for non-null and > 0 values
    mask = (
        df["bulk_modulus"].notna() & 
        (df["bulk_modulus"] > 0) &
        df["shear_modulus"].notna() & 
        (df["shear_modulus"] > 0)
    )
    
    filtered_df = df[mask].reset_index(drop=True)
    final_count = len(filtered_df)

    log_info_with_context(
        logger, 
        f"Filter complete. Kept {final_count} rows ({initial_count - final_count} removed)."
    )

    return filtered_df

def save_processed_data(df: pd.DataFrame, output_path: str) -> bool:
    """
    Saves the processed dataframe to a CSV file.

    Args:
        df: The dataframe to save.
        output_path: The path to the output CSV file.

    Returns:
        True if successful, False otherwise.
    """
    if df.empty:
        log_warning_with_context(logger, "Cannot save empty dataframe")
        return False

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_csv(output_path, index=False)
        log_info_with_context(logger, f"Saved processed data to {output_path}")
        return True
    except Exception as e:
        log_error_with_context(logger, f"Failed to save data to {output_path}: {str(e)}")
        return False

def main():
    """
    Main entry point for data ingestion.
    
    1. Loads configuration.
    2. Fetches OQMD data.
    3. Filters for valid Bulk/Shear moduli.
    4. Checks minimum row count (US-1 Acceptance 1).
    5. Saves to data/processed/encoded_alloys.csv (intermediate step for T015).
    """
    try:
        # Load configuration
        config = get_config()
        verify_config(config)

        output_path = os.path.join(
            config.get("paths", {}).get("processed_dir", "data/processed"),
            "encoded_alloys.csv"
        )

        log_info_with_context(logger, "Starting Data Ingestion Pipeline")

        # 1. Load Data
        raw_df = load_oqmd_data()
        if raw_df is None:
            log_error_with_context(logger, "Data loading failed. Aborting.")
            sys.exit(1)

        # 2. Filter Data
        valid_df = filter_valid_entries(raw_df)
        
        if valid_df.empty:
            log_error_with_context(logger, "No valid entries found after filtering.")
            sys.exit(1)

        # 3. Check Minimum Row Count (US-1 Acceptance 1)
        min_rows = config.get("data", {}).get("min_valid_rows", 500)
        if len(valid_df) < min_rows:
            log_warning_with_context(
                logger, 
                f"Insufficient data for statistical analysis (N={len(valid_df)} < {min_rows}). "
                f"Exiting gracefully as per US-1 acceptance criteria."
            )
            # Even if insufficient, we save what we have for inspection, 
            # but the script exits with code 0 as requested by the task description
            # to indicate a "graceful failure" rather than a crash.
            save_processed_data(valid_df, output_path)
            sys.exit(0)

        # 4. Save Data
        if not save_processed_data(valid_df, output_path):
            log_error_with_context(logger, "Failed to save processed data.")
            sys.exit(1)

        log_info_with_context(logger, "Data Ingestion Pipeline completed successfully.")
        sys.exit(0)

    except Exception as e:
        log_error_with_context(logger, f"Unexpected error in main pipeline: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()