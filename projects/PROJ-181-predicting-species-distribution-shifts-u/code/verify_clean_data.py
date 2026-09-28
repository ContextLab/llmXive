"""
Task T017: Create data/processed/occurrence_clean.csv and verify non-null climate values.

This script takes the output from T014b (filtered variable selection) and performs
final validation. It writes the final clean dataset to data/processed/occurrence_clean.csv.

Logic:
1. Load the preprocessed dataset from T014b (data/processed/occurrence_selected.csv).
2. Identify climate columns (all columns except metadata and coordinates).
3. Check for missing values in climate columns.
4. If missing values exist:
   - If caused by coordinates outside raster bounds (unfixable): EXIT with code 1.
   - If caused by other reasons (fixable via nearest neighbor): LOG warning and proceed (T007 handles imputation logic, but here we ensure the data is ready).
   - Note: The task description says "exit with code 1 ONLY if unfixable... otherwise log a warning".
     We assume T007 (data_utils) handles the actual imputation if called, but this task
     focuses on the *verification* and *final write*.
5. Write the final dataset to data/processed/occurrence_clean.csv.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import DATA_DIR, LOGS_DIR
from utils.data_utils import handle_missing_values, validate_coordinates

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "t017_validation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("t017_clean_data")

# Define paths
# T014b output is expected at this path based on the task dependency chain
INPUT_PATH = DATA_DIR / "processed" / "occurrence_selected.csv"
OUTPUT_PATH = DATA_DIR / "processed" / "occurrence_clean.csv"

# Ensure output directory exists
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_climate_columns(df: pd.DataFrame) -> list:
    """Identify climate variable columns (exclude metadata and coordinates)."""
    exclude_cols = {
        'source_identifier', 'download_timestamp', 'original_dataset_name',
        'species', 'decimalLatitude', 'decimalLongitude', 'eventDate'
    }
    climate_cols = [col for col in df.columns if col not in exclude_cols]
    return climate_cols

def main():
    logger.info(f"Starting T017 validation for {INPUT_PATH}")

    if not INPUT_PATH.exists():
        logger.error(f"Input file not found: {INPUT_PATH}. Did T014b run successfully?")
        sys.exit(1)

    try:
        df = pd.read_csv(INPUT_PATH)
        logger.info(f"Loaded {len(df)} records from {INPUT_PATH}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)

    if df.empty:
        logger.warning("Input dataset is empty. Creating empty output.")
        df.to_csv(OUTPUT_PATH, index=False)
        return

    climate_cols = get_climate_columns(df)
    logger.info(f"Identified {len(climate_cols)} climate columns: {climate_cols}")

    # Check for missing values in climate columns
    missing_mask = df[climate_cols].isnull().any(axis=1)
    missing_count = missing_mask.sum()

    if missing_count > 0:
        logger.warning(f"Found {missing_count} records with missing climate values.")
        
        # Attempt to identify if missing values are due to coordinates outside bounds
        # We check if the coordinates are valid for the raster extent (simplified check)
        # A more robust check would load the rasters, but we assume T014 extraction logic
        # already flagged these. Here we check if the coordinates themselves are valid.
        invalid_coords = ~validate_coordinates(df[['decimalLatitude', 'decimalLongitude']])
        
        if invalid_coords.any():
            logger.error(f"Found {invalid_coords.sum()} records with invalid coordinates (outside raster bounds).")
            logger.error("This is unfixable missing data. Exiting with code 1.")
            sys.exit(1)
        
        # If we are here, missing values are fixable (e.g., nearest neighbor imputation)
        # We log a warning as per task requirement.
        # Note: T007 (data_utils) has the imputation logic. We could call it here,
        # but the task says "verify... exit if unfixable... otherwise log".
        # To be safe and produce a clean CSV, we perform the imputation now.
        logger.info("Imputing missing values via nearest neighbor (as per T007).")
        df = handle_missing_values(df, climate_cols)
        
        # Verify imputation worked
        remaining_missing = df[climate_cols].isnull().any(axis=1).sum()
        if remaining_missing > 0:
            logger.error(f"Imputation failed. {remaining_missing} records still have missing values.")
            sys.exit(1)
        else:
            logger.info("Imputation successful. All climate values are now non-null.")
    else:
        logger.info("No missing climate values found.")

    # Final check: ensure no nulls in climate columns
    final_missing = df[climate_cols].isnull().sum().sum()
    if final_missing > 0:
        logger.error(f"Final check failed: {final_missing} missing values remain.")
        sys.exit(1)

    # Write output
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Successfully wrote {len(df)} clean records to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
