"""
Ingest verified kinetic dataset into data/assets/kinetic_dataset.csv with schema validation.

This script loads the raw kinetic dataset (downloaded by T009d), validates its schema
against expected columns and data types, and writes the clean dataset to the assets directory.
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
KINETIC_SCHEMA = {
    'molecule_id': str,
    'smiles': str,
    'reaction_type': str,
    'experimental_rate': float,
    'temperature_k': float,
    'solvent': str,
    'literature_ref': str,
    'confidence_score': float
}

REQUIRED_COLUMNS = list(KINETIC_SCHEMA.keys())

def setup_script_logging() -> logging.Logger:
    """Configure logging for this script."""
    logger = logging.getLogger('ingest_kinetic_data')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

def validate_schema(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validate that the dataframe matches the expected schema.

    Returns True if valid, False otherwise.
    """
    # Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False

    extra_cols = set(df.columns) - set(REQUIRED_COLUMNS)
    if extra_cols:
        logger.warning(f"Extra columns found (will be dropped): {extra_cols}")

    # Validate data types for required columns
    for col, expected_type in KINETIC_SCHEMA.items():
        if col not in df.columns:
            continue

        if expected_type == float:
            # Try to convert to float
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
            except (ValueError, TypeError) as e:
                logger.error(f"Column '{col}' cannot be converted to float: {e}")
                return False

    # Check for null values in critical columns
    critical_cols = ['molecule_id', 'smiles', 'experimental_rate']
    for col in critical_cols:
        if df[col].isnull().any():
            logger.error(f"Column '{col}' contains null values")
            return False

    # Validate positive rate values
    if (df['experimental_rate'] <= 0).any():
        logger.error("Column 'experimental_rate' contains non-positive values")
        return False

    # Validate temperature range (reasonable for kinetic experiments)
    if (df['temperature_k'] < 200).any() or (df['temperature_k'] > 1000).any():
        logger.warning("Some temperature values are outside typical range (200-1000K)")

    logger.info(f"Schema validation passed. Rows: {len(df)}, Columns: {len(df.columns)}")
    return True

def ingest_kinetic_dataset(
    raw_path: str,
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Load, validate, and ingest the kinetic dataset.

    Args:
        raw_path: Path to the raw kinetic dataset CSV
        output_path: Path where the validated dataset will be saved
        logger: Optional logger instance

    Returns:
        True if ingestion successful, False otherwise
    """
    if logger is None:
        logger = setup_script_logging()

    logger.info(f"Loading raw kinetic dataset from: {raw_path}")
    
    if not os.path.exists(raw_path):
        logger.error(f"Raw file not found: {raw_path}")
        return False

    try:
        df = pd.read_csv(raw_path)
        logger.info(f"Loaded {len(df)} rows from {raw_path}")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return False

    # Validate schema
    if not validate_schema(df, logger):
        logger.error("Schema validation failed")
        return False

    # Ensure output directory exists
    ensure_directories()

    # Save validated dataset
    logger.info(f"Saving validated dataset to: {output_path}")
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved {len(df)} rows to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save dataset: {e}")
        return False

    # Calculate and log checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"Output file checksum (SHA-256): {checksum}")

    return True

def main():
    """Main entry point for the ingestion script."""
    logger = setup_script_logging()
    config = get_config()

    # Define paths
    raw_path = os.path.join(config['data_raw_dir'], 'kinetic_dataset_raw.csv')
    output_path = os.path.join(config['data_assets_dir'], 'kinetic_dataset.csv')

    logger.info("Starting kinetic dataset ingestion...")
    logger.info(f"Raw input: {raw_path}")
    logger.info(f"Output: {output_path}")

    success = ingest_kinetic_dataset(raw_path, output_path, logger)

    if success:
        logger.info("Ingestion completed successfully")
        sys.exit(0)
    else:
        logger.error("Ingestion failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
