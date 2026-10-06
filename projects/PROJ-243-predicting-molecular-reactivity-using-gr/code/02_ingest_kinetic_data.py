import os
import sys
import logging
import pandas as pd
from typing import Optional, Dict, List

# Ensure project root is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config, ensure_directories
from utils.loaders import calculate_sha256

def setup_script_logging(name: str) -> logging.Logger:
    """Configure logging for the script."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def validate_schema(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that the DataFrame contains the required columns.
    Raises ValueError if validation fails.
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Schema validation failed: Missing required columns: {missing}")
    
    # Check for empty SMILES
    if df['smiles'].isnull().any() or (df['smiles'] == '').any():
        raise ValueError("Schema validation failed: Found null or empty SMILES strings.")
    
    # Check for empty rate constants if present (optional but good practice)
    if 'rate_constant' in df.columns and df['rate_constant'].isnull().all():
        raise ValueError("Schema validation failed: Rate constant column is entirely empty.")

    return True

def ingest_kinetic_dataset(
    input_path: str, 
    output_path: str, 
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Ingest verified external kinetic data into the assets directory with schema validation.
    
    This function:
    1. Loads the raw kinetic dataset from the input path.
    2. Validates the schema (required columns: smiles, rate_constant, temperature, source_doi).
    3. Ensures the output directory exists.
    4. Saves the validated data to the output path.
    5. Computes and logs the SHA-256 checksum of the output file.
    
    Parameters
    ----------
    input_path : str
        Path to the raw kinetic dataset (e.g., data/raw/kinetic_dataset_raw.csv).
    output_path : str
        Path where the ingested dataset will be saved (e.g., data/assets/kinetic_dataset.csv).
    logger : logging.Logger, optional
        Logger instance. If None, a default logger is created.
    """
    if logger is None:
        logger = setup_script_logging("ingest_kinetic_data")

    logger.info(f"Starting ingestion of kinetic data from: {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load the dataset
    logger.info("Loading dataset...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # Define required schema based on T010d-script mapping
    # Expected columns: smiles, rate_constant, temperature, source_doi, reaction_type (optional but preferred)
    required_columns = ['smiles', 'rate_constant', 'temperature', 'source_doi']
    
    logger.info("Validating schema...")
    try:
        validate_schema(df, required_columns)
        logger.info("Schema validation passed.")
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        raise

    # Ensure output directory exists
    ensure_directories([output_path])

    # Save to assets
    logger.info(f"Saving ingested dataset to: {output_path}")
    df.to_csv(output_path, index=False)

    # Compute checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"Output file checksum (SHA-256): {checksum}")

    logger.info("Ingestion completed successfully.")

def main():
    """Main entry point for the script."""
    logger = setup_script_logging("ingest_kinetic_data")
    
    try:
        config = get_config()
        
        # Define paths based on project structure
        input_path = os.path.join(config['paths']['raw_data'], 'kinetic_dataset_raw.csv')
        output_path = os.path.join(config['paths']['assets'], 'kinetic_dataset.csv')
        
        ingest_kinetic_dataset(input_path, output_path, logger)
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()