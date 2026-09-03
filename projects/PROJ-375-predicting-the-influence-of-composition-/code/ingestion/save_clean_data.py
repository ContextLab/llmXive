import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

# Import from project modules based on API surface
from utils.io import compute_sha256, setup_logging
from ingestion.fetch_data import fetch_data
from features.descriptors import extract_descriptors
from utils.config import get_env_var

# Configure logging
logger = setup_logging()

REQUIRED_COLUMNS = [
    'composition',
    'cte',
    'mean_atomic_radius',
    'electronegativity_var',
    'vec',
    'size_mismatch'
]

def load_intermediate_data() -> pd.DataFrame:
    """
    Fetches data from APIs or fallback, calculates descriptors, and returns a DataFrame.
    This function orchestrates the pipeline up to the point of saving.
    """
    logger.info("Starting data ingestion and feature extraction pipeline.")
    
    # Fetch raw data
    df_raw = fetch_data()
    
    if df_raw is None or df_raw.empty:
        logger.error("No data returned from fetch_data. Pipeline cannot proceed.")
        return None

    logger.info(f"Fetched {len(df_raw)} raw entries.")

    # Calculate descriptors
    # Ensure 'composition' column exists before calling extract_descriptors
    if 'composition' not in df_raw.columns:
        raise ValueError("Raw data missing 'composition' column required for descriptors.")
    
    df_features = extract_descriptors(df_raw)
    
    if df_features is None or df_features.empty:
        logger.error("Descriptor extraction resulted in empty DataFrame.")
        return None

    logger.info(f"Extracted descriptors for {len(df_features)} entries.")
    return df_features

def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates that required columns are present and drops rows with missing values
    in critical columns.
    """
    logger.info("Validating and cleaning dataset.")
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns after descriptor extraction: {missing_cols}")
    
    # Drop rows with NaN in critical columns (cte and composition are essential)
    # We drop NaNs for all required columns to ensure a clean dataset for modeling
    initial_count = len(df)
    df_clean = df.dropna(subset=REQUIRED_COLUMNS)
    dropped_count = initial_count - len(df_clean)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing values in required columns.")
    
    if df_clean.empty:
        logger.error("Dataset is empty after cleaning. No valid entries found.")
        return None

    logger.info(f"Cleaned dataset contains {len(df_clean)} entries.")
    return df_clean

def write_manifest(output_path: Path, checksum: str) -> None:
    """
    Writes a JSON manifest file containing the checksum and metadata.
    """
    manifest_path = output_path.with_suffix('.json')
    manifest_data = {
        "file": output_path.name,
        "checksum_algorithm": "sha256",
        "checksum": checksum,
        "columns": REQUIRED_COLUMNS,
        "status": "cleaned"
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Manifest written to {manifest_path}")

def save_parquet_and_manifest(df: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the DataFrame to Parquet and generates a checksum manifest.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to Parquet
    logger.info(f"Saving cleaned dataset to {output_path}")
    df.to_parquet(output_path, index=False)
    
    # Compute checksum
    checksum = compute_sha256(str(output_path))
    logger.info(f"Computed SHA256 checksum: {checksum}")
    
    # Write manifest
    write_manifest(output_path, checksum)
    
    # Final validation
    loaded_df = pd.read_parquet(output_path)
    if not all(col in loaded_df.columns for col in REQUIRED_COLUMNS):
        raise RuntimeError("Saved file validation failed: missing columns.")
    
    logger.info("Successfully saved and validated clean dataset.")

def main():
    """
    Main entry point for the save clean data task.
    """
    try:
        # 1. Load and process data
        df_intermediate = load_intermediate_data()
        
        if df_intermediate is None:
            logger.error("Pipeline halted: No data to process.")
            sys.exit(1)
        
        # 2. Clean and validate
        df_clean = clean_and_validate(df_intermediate)
        
        if df_clean is None:
            logger.error("Pipeline halted: No valid data after cleaning.")
            sys.exit(1)
        
        # 3. Define output path
        output_path = Path("data/processed/clean_mg_data.parquet")
        
        # 4. Save to Parquet with manifest
        save_parquet_and_manifest(df_clean, output_path)
        
        logger.info("Task T022 completed successfully.")
        
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()