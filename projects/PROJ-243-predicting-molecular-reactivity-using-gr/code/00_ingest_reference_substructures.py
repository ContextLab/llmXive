import os
import sys
import logging
import pandas as pd
from typing import Optional

# Add project root to path to allow relative imports if run as script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.loaders import calculate_sha256
from config import get_config, ensure_directories

def setup_script_logging():
    """Configure logging for the ingestion script."""
    config = get_config()
    ensure_directories()
    logger = logging.getLogger('ingest_reference_substructures')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler for this specific script
        log_dir = os.path.join(config['paths']['artifacts'], 'logs')
        os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(log_dir, 'ingest_reference_substructures.log'))
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def validate_schema(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validate the schema of the reference substructures dataframe.
    Expected columns based on typical chemical reactivity data:
    - 'substructure_id': Unique identifier
    - 'smiles': SMILES string of the substructure
    - 'name': Human-readable name
    - 'reactivity_class': Classification of reactivity
    - 'source_literature': Citation or source reference
    
    Returns True if valid, raises ValueError otherwise.
    """
    required_columns = {'substructure_id', 'smiles', 'name', 'reactivity_class', 'source_literature'}
    existing_columns = set(df.columns)
    
    missing_cols = required_columns - existing_columns
    if missing_cols:
        error_msg = f"Schema validation failed: Missing required columns: {missing_cols}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validate SMILES format (basic check: not empty, contains valid chars)
    if df['smiles'].isna().any():
        logger.warning("Found NaN values in 'smiles' column. Dropping rows.")
        df.dropna(subset=['smiles'], inplace=True)
    
    if df['smiles'].str.strip().eq('').any():
        logger.warning("Found empty strings in 'smiles' column. Dropping rows.")
        df = df[df['smiles'].str.strip().ne('')]
        
    logger.info(f"Schema validation passed. {len(df)} rows remaining.")
    return True

def ingest_reference_substructures(raw_path: str, output_path: str, logger: logging.Logger) -> None:
    """
    Ingest raw reference substructures data, validate schema, and save to assets.
    
    Args:
        raw_path: Path to the raw CSV file (data/raw/reference_substructures_raw.csv)
        output_path: Path for the ingested CSV file (data/assets/reference_substructures.csv)
        logger: Logger instance
    """
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    
    logger.info(f"Loading raw data from {raw_path}")
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to read raw CSV: {e}")
        raise
    
    logger.info(f"Loaded {len(df)} rows from raw file.")
    
    # Validate schema
    validate_schema(df, logger)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to assets
    logger.info(f"Saving validated data to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Verify checksum of output for consistency
    output_sha = calculate_sha256(output_path)
    logger.info(f"Output file SHA-256: {output_sha}")
    
    logger.info("Ingestion completed successfully.")

def main():
    """Main entry point for the ingestion script."""
    logger = setup_script_logging()
    config = get_config()
    
    raw_path = os.path.join(config['paths']['data_raw'], 'reference_substructures_raw.csv')
    output_path = os.path.join(config['paths']['data_assets'], 'reference_substructures.csv')
    
    try:
        ingest_reference_substructures(raw_path, output_path, logger)
        logger.info("Task T009c completed successfully.")
    except Exception as e:
        logger.error(f"Task T009c failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
