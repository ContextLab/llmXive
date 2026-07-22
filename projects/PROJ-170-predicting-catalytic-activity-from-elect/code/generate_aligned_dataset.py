"""
Task T020: Generate the final aligned dataset CSV.

This script loads the preprocessed and scaled data from the intermediate
files produced by the preprocessing pipeline and saves the final
`aligned_dataset.csv` to `data/processed/`.

It validates the schema to ensure all required columns are present before saving.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

# Import from local modules
from config import get_project_root, get_data_path, get_output_path
from logging_config import setup_logging, get_logger
from preprocess import load_raw_oc20_data, align_entries, retrieve_target_variable, impute_descriptors_knn, scale_features

# Constants
FINAL_SCHEMA_COLUMNS = [
    "composition",
    "surface_facet",
    "energy_change",
    "d_band_center",
    "adsorption_energy",
    # Add other numeric descriptors if they were scaled and kept
]

def validate_final_schema(df: pd.DataFrame, expected_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validates that the DataFrame contains all expected columns.
    Returns (is_valid, missing_columns).
    """
    missing = [col for col in expected_columns if col not in df.columns]
    return len(missing) == 0, missing

def main():
    setup_logging()
    logger = get_logger("generate_aligned_dataset")
    
    project_root = get_project_root()
    data_path = get_data_path()
    processed_path = data_path / "processed"
    
    # Ensure output directory exists
    processed_path.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_path / "aligned_dataset.csv"
    
    logger.info(f"Starting generation of aligned dataset to {output_file}")
    
    # Load the imputed dataset (produced by T017)
    # The path assumes the standard pipeline flow: data/processed/imputed_dataset.csv
    imputed_file = processed_path / "imputed_dataset.csv"
    
    if not imputed_file.exists():
        logger.error(f"Required intermediate file not found: {imputed_file}")
        logger.error("Please ensure T017 (imputation) has been run successfully.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(imputed_file)
        logger.info(f"Loaded {len(df)} rows from {imputed_file}")
    except Exception as e:
        logger.error(f"Failed to load {imputed_file}: {e}")
        sys.exit(1)
    
    # Validate schema
    is_valid, missing_cols = validate_final_schema(df, FINAL_SCHEMA_COLUMNS)
    
    if not is_valid:
        logger.error(f"Schema validation failed. Missing columns: {missing_cols}")
        logger.error("The preprocessing pipeline did not produce the expected columns.")
        sys.exit(1)
    
    # Check for NaN in the target column (energy_change) as a final sanity check
    # Although T017 should have imputed this, we ensure it for the final output.
    if df["energy_change"].isna().any():
        logger.warning("NaN values detected in 'energy_change' column after imputation. Excluding these rows.")
        df = df.dropna(subset=["energy_change"])
        logger.info(f"Dropped {len(df) - len(df)} rows with missing target. Final count: {len(df)}")
    
    # Ensure specific columns are in the correct order (optional but good practice)
    # We keep all columns present in the imputed dataset, but ensure the required ones are first
    # or just save as is if the schema is satisfied.
    
    # Save to CSV
    try:
        df.to_csv(output_file, index=False)
        logger.info(f"Successfully saved aligned dataset to {output_file}")
        logger.info(f"Total rows: {len(df)}, Total columns: {len(df.columns)}")
        logger.info(f"Columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to save {output_file}: {e}")
        sys.exit(1)
    
    # Verify the file exists and is not empty
    if not output_file.exists() or output_file.stat().st_size == 0:
        logger.error(f"Output file {output_file} is missing or empty after save.")
        sys.exit(1)
    
    logger.info("T020 completed successfully.")

if __name__ == "__main__":
    main()