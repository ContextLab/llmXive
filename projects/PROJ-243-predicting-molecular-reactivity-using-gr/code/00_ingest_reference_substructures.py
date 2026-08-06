import os
import sys
import logging
import pandas as pd
from typing import Optional

# Import from existing API surface
from utils.loaders import calculate_sha256
from config import get_config, ensure_directories

def setup_script_logging() -> logging.Logger:
    """Configure logging for the ingestion script."""
    logger = logging.getLogger(__name__)
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
    Validate that the dataframe contains the required columns for reference substructures.
    Expected columns: 'substructure_id', 'smiles', 'source', 'reaction_type' (or similar).
    Returns True if valid, False otherwise.
    """
    required_columns = {'substructure_id', 'smiles', 'source'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        logger.error(f"Schema validation failed. Missing columns: {missing}")
        return False
    
    # Check for empty dataframe
    if df.empty:
        logger.warning("Input dataframe is empty.")
        return False
    
    # Check for empty SMILES strings
    if df['smiles'].astype(str).str.strip().eq('').all():
        logger.error("All SMILES entries are empty.")
        return False
        
    logger.info(f"Schema validation passed. Columns: {list(df.columns)}")
    return True

def ingest_reference_substructures(
    input_path: str,
    output_path: str,
    logger: logging.Logger
) -> bool:
    """
    Load the raw reference substructures, validate schema, and save to assets.
    
    Args:
        input_path: Path to the raw CSV file (data/raw/reference_substructures_raw.csv)
        output_path: Path for the processed CSV file (data/assets/reference_substructures.csv)
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load raw data
        logger.info(f"Loading raw data from {input_path}")
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return False
        
        df = pd.read_csv(input_path)
        
        # Validate schema
        if not validate_schema(df, logger):
            return False
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save processed data
        logger.info(f"Saving validated data to {output_path}")
        df.to_csv(output_path, index=False)
        
        # Log checksum of output
        output_hash = calculate_sha256(output_path)
        logger.info(f"Output file checksum (SHA-256): {output_hash}")
        
        logger.info("Ingestion completed successfully.")
        return True
        
    except pd.errors.EmptyDataError:
        logger.error("Input file is empty.")
        return False
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        return False

def main() -> int:
    """Main entry point for the ingestion script."""
    logger = setup_script_logging()
    config = get_config()
    
    # Define paths based on project structure
    input_path = os.path.join('data', 'raw', 'reference_substructures_raw.csv')
    output_path = os.path.join('data', 'assets', 'reference_substructures.csv')
    
    # Ensure directories exist
    ensure_directories()
    
    # Run ingestion
    success = ingest_reference_substructures(input_path, output_path, logger)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
