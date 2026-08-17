import os
import sys
import logging
import pandas as pd
from typing import Optional

# Import from existing API surface
from utils.loaders import calculate_sha256
from config import get_config, ensure_directories

def setup_script_logging() -> logging.Logger:
    """Initialize logging for the ingestion script."""
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
    Validate that the DataFrame has the required columns and valid data types.
    Required columns: id, smiles, source_doi, description
    """
    required_columns = ['id', 'smiles', 'source_doi', 'description']
    
    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    
    # Check for empty DataFrame
    if df.empty:
        logger.error("DataFrame is empty after loading")
        return False
    
    # Validate SMILES format (basic check: non-empty strings)
    invalid_smiles = df[df['smiles'].isna() | (df['smiles'].astype(str).str.strip() == '')]
    if not invalid_smiles.empty:
        logger.warning(f"Found {len(invalid_smiles)} rows with invalid/empty SMILES. These will be excluded.")
        df = df.dropna(subset=['smiles'])
        df = df[df['smiles'].astype(str).str.strip() != '']
    
    # Ensure IDs are unique
    if df['id'].duplicated().any():
        logger.warning("Duplicate IDs found. Keeping first occurrence.")
        df = df.drop_duplicates(subset=['id'], keep='first')
    
    logger.info(f"Schema validation passed. {len(df)} valid records.")
    return True

def ingest_reference_substructures(
    input_path: str,
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Ingest verified reference substructures from raw CSV to assets CSV with schema validation.
    
    Args:
        input_path: Path to the raw CSV file (e.g., data/raw/reference_substructures_raw.csv)
        output_path: Path to the output CSV file (e.g., data/assets/reference_substructures.csv)
        logger: Optional logger instance
    
    Returns:
        True if ingestion was successful, False otherwise
    """
    if logger is None:
        logger = setup_script_logging()
    
    logger.info(f"Starting ingestion from {input_path}")
    
    # Check if input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return False
    
    try:
        # Load raw data
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return False
    
    # Validate schema
    if not validate_schema(df, logger):
        logger.error("Schema validation failed. Aborting ingestion.")
        return False
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        logger.info(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Write to output CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(df)} records to {output_path}")
        
        # Compute and log SHA-256 checksum
        checksum = calculate_sha256(output_path)
        logger.info(f"Output file SHA-256: {checksum}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        return False

def main() -> int:
    """Main entry point for the ingestion script."""
    logger = setup_script_logging()
    
    # Get configuration
    config = get_config()
    ensure_directories(config)
    
    # Define paths based on task requirements
    input_path = os.path.join(config['data_dir'], 'raw', 'reference_substructures_raw.csv')
    output_path = os.path.join(config['data_dir'], 'assets', 'reference_substructures.csv')
    
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    success = ingest_reference_substructures(input_path, output_path, logger)
    
    if success:
        logger.info("Ingestion completed successfully.")
        return 0
    else:
        logger.error("Ingestion failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
