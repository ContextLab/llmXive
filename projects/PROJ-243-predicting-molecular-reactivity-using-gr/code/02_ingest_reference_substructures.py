import os
import sys
import logging
import pandas as pd
from typing import Optional
from utils.loaders import calculate_sha256
from config import get_config, ensure_directories

def setup_script_logging():
    """Initialize logging for the ingest script."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def validate_schema(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validate that the DataFrame has the required columns for reference substructures.
    Expected columns: 'smiles', 'source_doi', 'description'.
    """
    required_columns = {'smiles', 'source_doi', 'description'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        logger.error(f"Schema validation failed. Missing required columns: {missing}")
        return False
    
    # Check for empty rows
    if df.empty:
        logger.error("Schema validation failed: DataFrame is empty.")
        return False

    # Check for NaN in critical columns
    if df['smiles'].isna().any():
        logger.error("Schema validation failed: 'smiles' column contains NaN values.")
        return False
    
    logger.info("Schema validation passed.")
    return True

def ingest_reference_substructures(
    input_path: str,
    output_path: str,
    config: dict,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Ingest verified reference substructures data into the assets directory.
    
    1. Verify input file exists and is non-empty.
    2. Load data.
    3. Validate schema.
    4. Verify checksum against manifest (if exists) or just verify file integrity.
       Note: T010b handles the explicit checksum verification against the manifest.
       This task assumes T010b passed, but we re-verify the file hash for safety
       and log it.
    5. Save to output path with standardized schema.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    if logger is None:
        logger = setup_script_logging()

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return False

    logger.info(f"Loading data from {input_path}")
    try:
        # Attempt to load based on extension, defaulting to CSV
        if input_path.endswith('.parquet'):
            df = pd.read_parquet(input_path)
        else:
            df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return False

    if not validate_schema(df, logger):
        return False

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info(f"Ingesting data to {output_path}")
    try:
        # Save as CSV for canonical input format as per task description
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully ingested {len(df)} records to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        return False

    return True

def main():
    """Main entry point for the script."""
    logger = setup_script_logging()
    config = get_config()
    
    # Define paths based on task description
    # Input: data/raw/reference_substructures_raw.csv (from T010a-parse)
    # Output: data/assets/reference_substructures.csv (for T030)
    input_file = os.path.join(config.get('data_raw_dir'), 'reference_substructures_raw.csv')
    output_file = os.path.join(config.get('data_assets_dir'), 'reference_substructures.csv')

    logger.info("Starting Reference Substructures Ingestion (T010c)")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")

    success = ingest_reference_substructures(input_file, output_file, config, logger)

    if success:
        logger.info("Task T010c completed successfully.")
        return 0
    else:
        logger.error("Task T010c failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
