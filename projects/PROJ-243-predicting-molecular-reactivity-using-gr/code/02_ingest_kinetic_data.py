import os
import sys
import logging
import pandas as pd
from typing import Optional, Dict, List
from config import get_config, ensure_directories
from utils.loaders import calculate_sha256

# Import logging setup from the established pattern in other scripts
# We replicate the logic here to ensure independence, or import if available in utils
# Since utils.logging_utils exists, we use it for consistency
from utils.logging_utils import setup_logging, get_logger, log_metric, flush_metrics

def validate_schema(df: pd.DataFrame, expected_columns: List[str]) -> bool:
    """
    Validates that the dataframe contains the expected columns and non-null values.
    Returns True if valid, raises ValueError otherwise.
    """
    missing_cols = set(expected_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Check for nulls in critical columns (assuming 'smiles' and 'rate' are critical)
    critical_cols = [c for c in expected_columns if c in ['smiles', 'rate', 'reaction_type']]
    for col in critical_cols:
        if df[col].isnull().any():
            raise ValueError(f"Critical column '{col}' contains null values.")

    # Basic type check for rate (should be numeric)
    if not pd.api.types.is_numeric_dtype(df['rate']):
        raise ValueError(f"Column 'rate' must be numeric, found {df['rate'].dtype}")

    return True

def setup_script_logging(script_name: str = "02_ingest_kinetic_data"):
    """Sets up logging for the script."""
    return setup_logging(script_name)

def ingest_kinetic_dataset(
    input_path: str,
    output_path: str,
    expected_columns: List[str],
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Loads the raw kinetic dataset, validates schema, and saves to assets.
    
    Args:
        input_path: Path to the raw CSV (data/raw/kinetic_dataset_raw.csv)
        output_path: Path to the final asset (data/assets/kinetic_dataset.csv)
        expected_columns: List of required column names
        logger: Logger instance
        
    Returns:
        The validated DataFrame
    """
    logger.info(f"Loading raw kinetic data from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                              "Ensure T009d (download) and T009e (verify) completed successfully.")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    logger.info("Validating schema...")
    try:
        validate_schema(df, expected_columns)
        logger.info("Schema validation passed.")
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        raise

    # Ensure output directory exists
    ensure_directories([os.path.dirname(output_path)])

    logger.info(f"Saving validated dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Log the row count as a metric
    log_metric("ingested_kinetic_rows", len(df), logger=logger)
    
    return df

def main():
    """Main entry point for the ingestion script."""
    logger = setup_script_logging("02_ingest_kinetic_data")
    logger.info("Starting kinetic dataset ingestion (T009f).")
    
    config = get_config()
    
    # Define paths based on project structure
    raw_path = os.path.join(config['paths']['data_raw'], 'kinetic_dataset_raw.csv')
    asset_path = os.path.join(config['paths']['data_assets'], 'kinetic_dataset.csv')
    
    # Expected schema based on typical kinetic data requirements
    # Adjust if the specific dataset from T009d has different column names
    # Assuming standard: smiles, rate, reaction_type
    expected_columns = ['smiles', 'rate', 'reaction_type']
    
    try:
        ingest_kinetic_dataset(raw_path, asset_path, expected_columns, logger)
        logger.info("Kinetic dataset ingestion completed successfully.")
        log_metric("task_T009f_status", "success", logger=logger)
    except Exception as e:
        logger.error(f"Kinetic dataset ingestion failed: {e}")
        log_metric("task_T009f_status", "failed", logger=logger)
        sys.exit(1)
    finally:
        flush_metrics()

if __name__ == "__main__":
    main()
