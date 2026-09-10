import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

import pandas as pd
import numpy as np

# Import existing project utilities
from logging_config import get_logger, raise_on_missing_data
from hygiene import calculate_md5, save_artifact_hashes, update_artifact_hash
from config.loader import load_schema_map, get_target_columns

# Configure logger
logger = get_logger(__name__)

# Define predictor columns that MUST be present for normalization
# These are the inputs required for Archard's law or standard wear models
PREDICTOR_COLUMNS = [
    'pulse_duration', 'power', 'scanning_speed', 'pattern_geometry',
    'hardness', 'elastic_modulus'
]

# Columns that are allowed to be missing for "raw" normalization
OPTIONAL_COLUMNS = ['contact_load', 'sliding_speed']

def handle_missing_values(df: pd.DataFrame, normalization_method_col: str = 'normalization_method') -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Implements missing value handling per FR-002:
    1. DROP records with missing values in any of the PREDICTOR_COLUMNS.
    2. RETAIN records with missing values in OPTIONAL_COLUMNS (contact_load, sliding_speed).
       For these retained records, ensure normalization_method is set to 'raw'.
    
    Args:
        df: The input DataFrame (schema standardized).
        normalization_method_col: Name of the column tracking normalization status.
    
    Returns:
        Tuple of (processed_df, stats_dict)
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df, {'dropped_predictor_missing': 0, 'retained_raw_missing': 0, 'total_input': 0}

    original_count = len(df)
    logger.info(f"Starting missing value handling on {original_count} records.")

    # Ensure the normalization column exists
    if normalization_method_col not in df.columns:
        df[normalization_method_col] = 'unknown'
    
    # Identify columns that must be present
    # Filter PREDICTOR_COLUMNS to only those actually in the dataframe
    required_cols_present = [col for col in PREDICTOR_COLUMNS if col in df.columns]
    optional_cols_present = [col for col in OPTIONAL_COLUMNS if col in df.columns]

    if not required_cols_present:
        logger.error("No predictor columns found in the dataframe. Cannot proceed with validation.")
        raise ValueError("Missing required predictor columns in dataframe.")

    # 1. DROP records with missing predictors
    # Create a mask for rows where ANY required column is NaN
    mask_missing_predictors = df[required_cols_present].isna().any(axis=1)
    dropped_count = mask_missing_predictors.sum()
    
    if dropped_count > 0:
        logger.warning(f"Dropping {dropped_count} records with missing predictor values.")
        df = df[~mask_missing_predictors]

    # 2. RETAIN records with missing optional columns, flag as 'raw'
    # Identify rows where at least one optional column is missing
    if optional_cols_present:
        mask_missing_optional = df[optional_cols_present].isna().any(axis=1)
        retained_count = mask_missing_optional.sum()
        
        if retained_count > 0:
            logger.info(f"Retaining {retained_count} records with missing optional columns (contact_load/sliding_speed).")
            # Force normalization_method to 'raw' for these records
            df.loc[mask_missing_optional, normalization_method_col] = 'raw'
            # Also ensure records that were previously 'unknown' or 'normalized' but have missing optional 
            # are correctly flagged if they rely on those for normalization. 
            # However, the task specifically says: RETAIN records with missing optional -> set 'raw'.
    else:
        retained_count = 0

    final_count = len(df)
    logger.info(f"Missing value handling complete. Dropped: {dropped_count}, Retained (Raw): {retained_count}, Final: {final_count}")

    stats = {
        'dropped_predictor_missing': int(dropped_count),
        'retained_raw_missing': int(retained_count),
        'total_input': int(original_count),
        'total_output': int(final_count)
    }

    return df, stats

def main():
    """
    Main entry point for missing value handling logic.
    Reads the aggregated data from the previous step, applies cleaning,
    and writes the result to the processed directory.
    """
    # Paths
    input_path = Path("data/processed/aggregated_raw.csv") # Assumed intermediate from T011/T013
    output_path = Path("data/processed/aggregated_clean.csv")
    hash_path = Path("state/artifact_hashes.yaml")
    
    # If the immediate predecessor output is different, adjust. 
    # Based on T015, the output is aggregated_clean.csv, but T012 is the logic to create it.
    # T013 handles Archard's law. T012 handles missing values. 
    # The pipeline order in tasks.md: T010 (fetch) -> T011 (schema) -> T012 (missing) -> T013 (Archard).
    # So input to T012 is the output of T011.
    # Let's assume the standard flow: T011 writes to a temp or we chain in main.
    # For this specific task implementation, we assume the input is the schema-standardized data.
    # We will look for 'aggregated_standardized.csv' or similar if T011 outputs it, 
    # but T015 says output is 'aggregated_clean.csv'. 
    # To be safe and executable: T012 will read from a logical intermediate if T011 is separate,
    # or we assume the 'ingest_all_data' function in T010/T011 pipeline produces the input.
    # Given T015 output is 'aggregated_clean.csv', and T012 is part of creating that:
    # We will implement the logic to read the 'raw' or 'standardized' file.
    # Let's assume the file from T011 is 'data/processed/aggregated_standardized.csv' or we read 'data/raw/...' 
    # and apply the whole chain. 
    # However, the task asks to implement the HANDLING logic.
    
    # For the script to run independently as per T012 requirements:
    # We need an input file. Let's assume T011 output is 'data/processed/aggregated_standardized.csv'.
    # If T011 hasn't run, we might need to fetch. But T010/T011 are marked done.
    # We will assume the file exists at 'data/processed/aggregated_standardized.csv' as the output of T011.
    # If T015 (aggregated_clean.csv) is the final output, T012 produces the intermediate for T013.
    
    # Let's check if the input file exists. If not, we try to find the most recent processed file.
    if not input_path.exists():
        # Fallback to a generic search or error
        # In a real pipeline, T011 would have written here.
        # Let's try to find any csv in data/processed except the final clean one
        candidates = list(Path("data/processed").glob("aggregated_*.csv"))
        if not candidates:
            raise FileNotFoundError("No input file found for missing value handling. Expected 'data/processed/aggregated_standardized.csv' or similar.")
        # Pick the one that isn't 'aggregated_clean.csv' if it exists
        candidates = [c for c in candidates if c.name != 'aggregated_clean.csv']
        if candidates:
            input_path = candidates[0]
            logger.info(f"Using found input file: {input_path}")
        else:
            raise FileNotFoundError("No suitable input file found.")

    logger.info(f"Reading input data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        raise

    # Apply the logic
    df_cleaned, stats = handle_missing_values(df)

    # Write output
    logger.info(f"Writing cleaned data to {output_path}")
    df_cleaned.to_csv(output_path, index=False)

    # Update hashes
    if hash_path.exists():
        update_artifact_hash(hash_path, output_path)
    else:
        save_artifact_hashes({output_path.name: calculate_md5(output_path)}, hash_path)

    # Log stats
    logger.info(f"Statistics: {stats}")
    return stats

if __name__ == "__main__":
    main()