"""
Verify that occurrence_clean.csv has non-null climate values.
Exits with code 1 ONLY if unfixable missing data exists (e.g., coordinates outside raster bounds).
Otherwise logs a warning for imputed values.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, LOGS_DIR
from logging_config import get_pipeline_logger
from utils.yaml_utils import write_preprocess_counts

def main():
    logger = get_pipeline_logger("verify_clean_data")
    logger.info("Starting verification of occurrence_clean.csv")

    input_path = DATA_DIR / "processed" / "occurrence_clean.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Run T014 (extract_climate_variables) first to generate occurrence_clean.csv")
        sys.exit(1)

    # Load the data
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        sys.exit(1)

    # Identify climate columns (typically bio1-bio19)
    climate_cols = [col for col in df.columns if col.startswith('bio')]
    
    if not climate_cols:
        logger.error("No climate columns (bio*) found in the dataset.")
        logger.error("Expected columns like bio1, bio2, ..., bio19.")
        sys.exit(1)

    logger.info(f"Found {len(climate_cols)} climate columns: {climate_cols}")

    # Check for missing values in climate columns
    missing_counts = df[climate_cols].isnull().sum()
    total_missing = missing_counts.sum()

    if total_missing == 0:
        logger.info("Verification PASSED: All climate values are non-null.")
        logger.info("No unfixable missing data detected.")
        sys.exit(0)

    # If there are missing values, categorize them
    # Unfixable: coordinates outside raster bounds (typically represented as NaN after extraction)
    # Fixable: Imputed values (should already be handled by T014, but we check for any remaining)
    
    # Count rows with ANY missing climate value
    rows_with_missing = df[climate_cols].isnull().any(axis=1).sum()
    
    if rows_with_missing > 0:
        logger.warning(f"Found {rows_with_missing} records with missing climate values.")
        logger.warning("These are likely due to coordinates outside raster bounds (unfixable).")
        
        # Log details of missing data per column
        for col, count in missing_counts.items():
            if count > 0:
                logger.warning(f"  {col}: {count} missing values")
        
        logger.error("Unfixable missing data detected (coordinates outside raster bounds).")
        logger.error("Exiting with code 1 as per task requirements.")
        sys.exit(1)
    else:
        # This case shouldn't happen if total_missing > 0, but just in case
        logger.info("Verification PASSED: No unfixable missing data found.")
        sys.exit(0)

if __name__ == "__main__":
    main()