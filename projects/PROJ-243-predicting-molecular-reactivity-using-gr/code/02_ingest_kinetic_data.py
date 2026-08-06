"""
Ingest verified external kinetic data into data/assets/kinetic_dataset.csv with schema validation.

This script reads the verified raw kinetic dataset (data/raw/kinetic_dataset_raw.csv),
validates it against the expected schema, and saves the cleaned, validated data
to data/assets/kinetic_dataset.csv.

Prerequisites:
  - data/raw/kinetic_dataset_raw.csv must exist (produced by T010d)
  - data/raw/checksums.json must exist (produced by T010g/T010h)
"""
import os
import sys
import logging
import pandas as pd
from typing import Optional, Dict, List

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config, ensure_directories
from utils.loaders import calculate_sha256

# Expected schema for kinetic dataset
# Based on FR-009: external kinetic dataset of >=20 molecules with experimental reaction rates
EXPECTED_COLUMNS = [
    'molecule_id',
    'smiles',
    'reaction_type',
    'experimental_rate',
    'temperature_k',
    'solvent',
    'reference'
]

def setup_script_logging() -> logging.Logger:
    """Setup logging for the ingestion script."""
    logger = logging.getLogger('ingest_kinetic_data')
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)

    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger

def validate_schema(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate that the dataframe has the expected schema.

    Args:
        df: The dataframe to validate
        logger: Optional logger for error messages

    Returns:
        True if schema is valid, False otherwise
    """
    if logger is None:
        logger = logging.getLogger('ingest_kinetic_data')

    # Check required columns
    missing_columns = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing_columns:
        logger.error(f"Schema validation failed: missing columns {missing_columns}")
        return False

    # Check for minimum number of molecules (FR-009 requirement)
    if len(df) < 20:
        logger.error(f"Schema validation failed: dataset has {len(df)} molecules, requires >= 20")
        return False

    # Check for non-empty SMILES
    if df['smiles'].isnull().any() or (df['smiles'] == '').any():
        logger.error("Schema validation failed: empty or null SMILES found")
        return False

    # Check for positive experimental rates
    if 'experimental_rate' in df.columns:
        if (df['experimental_rate'] <= 0).any():
            logger.error("Schema validation failed: non-positive experimental rates found")
            return False

    logger.info(f"Schema validation passed: {len(df)} molecules, all required columns present")
    return True

def ingest_kinetic_dataset(
    raw_path: str,
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Ingest the verified kinetic dataset into the assets directory.

    Args:
        raw_path: Path to the verified raw dataset
        output_path: Path to save the ingested dataset
        logger: Optional logger

    Returns:
        True if ingestion successful, False otherwise
    """
    if logger is None:
        logger = logging.getLogger('ingest_kinetic_data')

    logger.info(f"Loading kinetic dataset from {raw_path}")

    if not os.path.exists(raw_path):
        logger.error(f"Raw kinetic dataset not found at {raw_path}")
        return False

    try:
        # Load the raw dataset
        df = pd.read_csv(raw_path)
        logger.info(f"Loaded {len(df)} rows from raw dataset")

    except Exception as e:
        logger.error(f"Failed to load raw dataset: {e}")
        return False

    # Validate schema
    if not validate_schema(df, logger):
        logger.error("Schema validation failed, aborting ingestion")
        return False

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        ensure_directories(output_dir)

    # Clean and standardize the data
    logger.info("Cleaning and standardizing data")

    # Strip whitespace from string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()

    # Ensure consistent column order
    df = df[EXPECTED_COLUMNS]

    # Save to output path
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved ingested dataset to {output_path}")

        # Verify the output file
        output_hash = calculate_sha256(output_path)
        logger.info(f"Output file SHA-256: {output_hash}")

    except Exception as e:
        logger.error(f"Failed to save ingested dataset: {e}")
        return False

    return True

def main() -> int:
    """Main entry point for the ingestion script."""
    logger = setup_script_logging()
    logger.info("Starting kinetic dataset ingestion")

    config = get_config()

    # Define paths
    raw_path = os.path.join('data', 'raw', 'kinetic_dataset_raw.csv')
    output_path = os.path.join('data', 'assets', 'kinetic_dataset.csv')

    # Perform ingestion
    success = ingest_kinetic_dataset(raw_path, output_path, logger)

    if success:
        logger.info("Kinetic dataset ingestion completed successfully")
        return 0
    else:
        logger.error("Kinetic dataset ingestion failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
