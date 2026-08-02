"""
Module to save the daily aggregates to CSV and validate against the schema.

This script is the final step of User Story 1. It:
1. Loads the processed daily aggregates from memory (computed by preprocess.py).
2. Writes them to `data/processed/daily_aggregates.csv`.
3. Validates the output against `specs/001-physical-activity-mood-variability/contracts/daily_aggregates.schema.yaml`.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config import get_path
from preprocess import compute_daily_aggregates, load_bronze_data
from output_validator import load_schema, validate_dataframe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_and_validate():
    """
    Main entry point for saving and validating daily aggregates.
    
    Returns:
        bool: True if successful and validation passes, False otherwise.
    """
    logger.info("Starting daily aggregates save and validation process.")
    
    # 1. Load and preprocess data to get the DataFrame
    # We re-run the computation here to ensure we have the latest state
    # based on the bronze data, or we could load from a temporary intermediate file.
    # Given the task flow, we assume preprocess.py logic is available to generate the DF.
    try:
        logger.info("Loading bronze data...")
        bronze_path = get_path("data_raw", "bronze.parquet")
        if not os.path.exists(bronze_path):
            raise FileNotFoundError(f"Bronze data not found at {bronze_path}. Please run T007 first.")
        
        df_bronze = load_bronze_data(bronze_path)
        
        logger.info("Computing daily aggregates...")
        # This function performs all the logic from T011-T015b
        df_aggregates = compute_daily_aggregates(df_bronze)
        
    except Exception as e:
        logger.error(f"Failed to compute daily aggregates: {e}")
        return False

    if df_aggregates is None or df_aggregates.empty:
        logger.error("Computed daily aggregates DataFrame is empty.")
        return False

    # 2. Define output path
    output_path = get_path("data_processed", "daily_aggregates.csv")
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Write to CSV
    try:
        logger.info(f"Writing daily aggregates to {output_path}...")
        df_aggregates.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(df_aggregates)} rows to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write CSV: {e}")
        return False

    # 4. Validate against schema
    schema_path = get_path("specs", "001-physical-activity-mood-variability/contracts/daily_aggregates.schema.yaml")
    
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at {schema_path}. Cannot validate.")
        return False

    try:
        logger.info(f"Loading schema from {schema_path}...")
        schema = load_schema(schema_path)
        
        logger.info("Validating DataFrame against schema...")
        is_valid, errors = validate_dataframe(df_aggregates, schema)
        
        if is_valid:
            logger.info("Validation PASSED: daily_aggregates.csv conforms to the schema.")
            return True
        else:
            logger.error("Validation FAILED: Schema errors found:")
            for err in errors:
                logger.error(f"  - {err}")
            return False
            
    except Exception as e:
        logger.error(f"Validation process failed with error: {e}")
        return False

def main():
    """CLI entry point."""
    success = save_and_validate()
    if not success:
        logger.error("Process terminated with errors.")
        sys.exit(1)
    else:
        logger.info("Process completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
