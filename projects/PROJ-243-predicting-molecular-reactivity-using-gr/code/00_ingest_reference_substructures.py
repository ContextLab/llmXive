import os
import sys
import logging
import pandas as pd
from typing import Optional

from utils.loaders import calculate_sha256
from config import get_config, ensure_directories

# Import the schema validation logic from the same module context
# or define it here if it's specific to this task flow.
# Based on the API surface, we define validate_schema locally or assume it exists.
# Since the API surface lists 'validate_schema' as a public name in this file,
# we must define it here.

def validate_schema(df: pd.DataFrame, expected_columns: list) -> bool:
    """
    Validates that the dataframe contains the expected columns.
    Returns True if valid, raises ValueError otherwise.
    """
    missing = set(expected_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Schema validation failed. Missing columns: {missing}")
    
    # Check for empty dataframe
    if df.empty:
        raise ValueError("Schema validation failed. Dataframe is empty.")
    
    # Basic type checks if needed, but column presence is the primary check here
    logging.info(f"Schema validation passed for {len(df)} rows.")
    return True

def setup_script_logging():
    """Sets up logging for the ingestion script."""
    config = get_config()
    ensure_directories(config)
    
    log_file = os.path.join(config['paths']['log_dir'], 'ingest_reference_substructures.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def ingest_reference_substructures(logger: logging.Logger, raw_path: str, asset_path: str, checksums_path: str) -> None:
    """
    Ingests the verified reference substructures from the raw CSV to the assets CSV.
    Performs schema validation and ensures the output directory exists.
    
    Args:
        logger: Logger instance.
        raw_path: Path to the verified raw CSV file.
        asset_path: Path where the ingested CSV will be saved.
        checksums_path: Path to the checksums manifest (for reference/logging).
    """
    logger.info(f"Starting ingestion from {raw_path} to {asset_path}")
    
    # Load the raw data
    try:
        df = pd.read_csv(raw_path)
    except FileNotFoundError:
        logger.error(f"Raw file not found: {raw_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to read raw file: {e}")
        raise

    # Define expected schema based on FR-008 context (SMILES based)
    # Typically: substructure_name, smiles, description, source
    # We validate against the columns present in the generated file if specific ones aren't mandated,
    # but usually, a 'smiles' column is critical.
    # Let's assume the generator produced: 'name', 'smiles', 'description'
    # We will validate that 'smiles' exists as a critical column.
    critical_columns = ['smiles']
    
    try:
        validate_schema(df, critical_columns)
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        raise

    # Ensure output directory exists
    os.makedirs(os.path.dirname(asset_path), exist_ok=True)

    # Save to assets
    # Use index=False to avoid adding an extra index column
    df.to_csv(asset_path, index=False)
    
    # Verify the output file was created and log its hash
    if os.path.exists(asset_path):
        output_hash = calculate_sha256(asset_path)
        logger.info(f"Ingestion complete. Saved to {asset_path}")
        logger.info(f"Output file SHA-256: {output_hash}")
    else:
        logger.error("Ingestion failed: Output file was not created.")
        raise RuntimeError("Output file creation failed.")

def main():
    """Main entry point for the ingestion script."""
    logger = setup_script_logging()
    config = get_config()
    
    raw_path = os.path.join(config['paths']['raw_data_dir'], 'reference_substructures_raw.csv')
    asset_path = os.path.join(config['paths']['assets_dir'], 'reference_substructures.csv')
    checksums_path = os.path.join(config['paths']['raw_data_dir'], 'checksums.json')
    
    try:
        ingest_reference_substructures(logger, raw_path, asset_path, checksums_path)
        logger.info("Task T009c completed successfully.")
    except Exception as e:
        logger.error(f"Task T009c failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
