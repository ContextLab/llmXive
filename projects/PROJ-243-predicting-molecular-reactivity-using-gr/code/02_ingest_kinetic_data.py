"""
Task T010f: Ingest verified external kinetic data into data/assets/kinetic_dataset.csv
with schema validation.
"""
import os
import sys
import logging
import pandas as pd
from typing import Optional, Dict, List

# Import from project utils as per API surface
from config import get_config, ensure_directories
from utils.loaders import calculate_sha256

# Configure logging
def setup_script_logging() -> logging.Logger:
    """Setup logging for this script."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def validate_schema(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validate the schema of the kinetic dataset.
    
    Expected columns: id, smiles, rate_constant, temperature, source_doi
    
    Args:
        df: DataFrame to validate
        logger: Logger instance
        
    Returns:
        True if schema is valid, False otherwise
    """
    required_columns = {'id', 'smiles', 'rate_constant', 'temperature', 'source_doi'}
    actual_columns = set(df.columns)
    
    missing_columns = required_columns - actual_columns
    if missing_columns:
        logger.error(f"Schema validation failed: missing columns {missing_columns}")
        return False
    
    # Validate data types
    try:
        df['rate_constant'] = pd.to_numeric(df['rate_constant'], errors='raise')
        df['temperature'] = pd.to_numeric(df['temperature'], errors='raise')
    except (ValueError, TypeError) as e:
        logger.error(f"Schema validation failed: invalid data types - {e}")
        return False
    
    # Validate non-empty SMILES
    if df['smiles'].isnull().any() or (df['smiles'] == '').any():
        logger.error("Schema validation failed: empty or null SMILES found")
        return False
    
    logger.info("Schema validation passed")
    return True

def ingest_kinetic_dataset(
    input_path: str,
    output_path: str,
    logger: logging.Logger
) -> bool:
    """
    Ingest kinetic dataset from raw to assets with schema validation.
    
    Args:
        input_path: Path to the raw kinetic dataset CSV
        output_path: Path to write the validated assets CSV
        logger: Logger instance
        
    Returns:
        True if ingestion successful, False otherwise
    """
    logger.info(f"Reading kinetic dataset from {input_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return False
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        return False
    
    logger.info(f"Read {len(df)} rows from {input_path}")
    
    # Validate schema
    if not validate_schema(df, logger):
        logger.error("Schema validation failed. Aborting ingestion.")
        return False
    
    # Ensure output directory exists
    ensure_directories([os.path.dirname(output_path)])
    
    # Write to output
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote validated dataset to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        return False
    
    # Compute and log checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"SHA-256 checksum of output file: {checksum}")
    
    return True

def main():
    """Main entry point for T010f."""
    logger = setup_script_logging()
    logger.info("Starting T010f: Ingest Kinetic Data")
    
    config = get_config()
    
    # Define paths
    input_path = config.get('paths', {}).get('kinetic_raw', 
                     os.path.join('data', 'raw', 'kinetic_dataset_raw.csv'))
    output_path = config.get('paths', {}).get('kinetic_assets', 
                       os.path.join('data', 'assets', 'kinetic_dataset.csv'))
    
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    success = ingest_kinetic_dataset(input_path, output_path, logger)
    
    if success:
        logger.info("T010f completed successfully")
        return 0
    else:
        logger.error("T010f failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())