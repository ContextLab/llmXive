"""
Preprocess raw data: clean, filter, and save features.

This script performs the following steps:
1. Loads raw data from `data/processed/raw_features.csv` (output of descriptors.py).
2. Validates the schema against `specs/001-predicting-the-stability-of-perovskite-s/contracts/data-schema.yaml`.
3. Cleans data:
   - Drops rows where `decomposition_energy` is null.
   - Drops rows where ANY feature column (`tolerance_factor`, `octahedral_factor`,
     `ionic_radius_mismatch`, `electronegativity_diff`) is null.
4. Logs excluded rows to `logs/pipeline.log`.
5. Saves the cleaned dataframe to `data/processed/features.csv`.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import yaml

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event

# Configure logger
logger = get_logger(__name__)

# Define paths relative to project root
RAW_DATA_PATH = project_root / "data" / "processed" / "raw_features.csv"
OUTPUT_PATH = project_root / "data" / "processed" / "features.csv"
SCHEMA_PATH = project_root / "specs" / "001-predicting-the-stability-of-perovskite-s" / "contracts" / "data-schema.yaml"

# Feature columns required for the model
FEATURE_COLUMNS = [
    "tolerance_factor",
    "octahedral_factor",
    "ionic_radius_mismatch",
    "electronegativity_diff"
]
TARGET_COLUMN = "decomposition_energy"

def load_raw_data() -> pd.DataFrame:
    """Load raw data from the CSV file."""
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Raw data file not found at {RAW_DATA_PATH}. "
            "Ensure code/data/descriptors.py has been run successfully."
        )
    
    logger.info(f"Loading raw data from {RAW_DATA_PATH}")
    df = pd.read_csv(RAW_DATA_PATH)
    log_pipeline_event(f"Loaded {len(df)} rows from raw data")
    return df

def validate_schema(df: pd.DataFrame) -> bool:
    """Validate the dataframe against the expected schema."""
    if not SCHEMA_PATH.exists():
        logger.warning(f"Schema file not found at {SCHEMA_PATH}. Skipping schema validation.")
        return True

    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)

    required_columns = set(schema.get('required_columns', []))
    actual_columns = set(df.columns)

    missing_columns = required_columns - actual_columns
    if missing_columns:
        error_msg = f"Schema validation failed: Missing required columns: {missing_columns}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Schema validation passed.")
    return True

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataframe by dropping rows with missing target or feature values.
    
    Steps:
    1. Drop rows where `decomposition_energy` is null.
    2. Drop rows where ANY of the feature columns are null.
    3. Log exclusion reasons.
    """
    initial_count = len(df)
    logger.info(f"Starting data cleaning. Initial rows: {initial_count}")

    # Step 1: Drop rows where target is null
    target_null_mask = df[TARGET_COLUMN].isnull()
    if target_null_mask.any():
        count = target_null_mask.sum()
        log_exclusion_reason(f"Missing {TARGET_COLUMN}", count)
        df = df.dropna(subset=[TARGET_COLUMN])
    
    # Step 2: Drop rows where ANY feature column is null
    feature_null_mask = df[FEATURE_COLUMNS].isnull().any(axis=1)
    if feature_null_mask.any():
        count = feature_null_mask.sum()
        log_exclusion_reason(f"Missing any feature in {FEATURE_COLUMNS}", count)
        df = df.dropna(subset=FEATURE_COLUMNS)

    final_count = len(df)
    excluded_count = initial_count - final_count
    
    log_pipeline_event(f"Data cleaning complete. Excluded {excluded_count} rows. Final rows: {final_count}")
    
    return df.reset_index(drop=True)

def save_processed_data(df: pd.DataFrame) -> None:
    """Save the processed dataframe to CSV."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving processed data to {OUTPUT_PATH}")
    df.to_csv(OUTPUT_PATH, index=False)
    
    log_pipeline_event(f"Successfully saved {len(df)} rows to {OUTPUT_PATH}")
    logger.info(f"Output file created: {OUTPUT_PATH}")

def main():
    """Main entry point for the preprocessing pipeline."""
    try:
        # Load raw data
        df = load_raw_data()
        
        # Validate schema
        validate_schema(df)
        
        # Clean data
        df_clean = clean_data(df)
        
        if len(df_clean) == 0:
            raise RuntimeError("Dataset empty after cleaning")

        # Verify no nulls in critical columns
        if df_clean[TARGET_COLUMN].isnull().any():
            raise ValueError(f"Target column '{TARGET_COLUMN}' still contains nulls after cleaning.")
        
        null_features = df_clean[FEATURE_COLUMNS].isnull().sum()
        if null_features.any():
            raise ValueError(f"Feature columns still contain nulls after cleaning:\n{null_features[null_features > 0]}")

        # Save processed data
        save_processed_data(df_clean)
        
        logger.info("Preprocessing pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation or cleaning error: {e}")
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        raise

if __name__ == "__main__":
    main()
