import os
import sys
import logging
import pandas as pd
from typing import Optional

# Import from local utils as defined in API surface
from utils.loaders import calculate_sha256
from config import get_config, ensure_directories

def setup_script_logging() -> logging.Logger:
    """Configure logging for the ingestion script."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def validate_schema(df: pd.DataFrame, expected_columns: list, logger: logging.Logger) -> bool:
    """
    Validate that the dataframe contains the expected columns.
    
    Args:
        df: The dataframe to validate.
        expected_columns: List of required column names.
        logger: Logger instance.
        
    Returns:
        True if valid, False otherwise.
    """
    missing = set(expected_columns) - set(df.columns)
    if missing:
        logger.error(f"Schema validation failed. Missing columns: {missing}")
        return False
    
    # Check for empty dataframe
    if df.empty:
        logger.error("Schema validation failed. Dataframe is empty.")
        return False
        
    logger.info(f"Schema validation passed. Found columns: {list(df.columns)}")
    return True

def ingest_reference_substructures(raw_path: str, output_path: str, logger: logging.Logger) -> None:
    """
    Ingest the verified raw reference substructures into the assets directory.
    
    This task performs:
    1. Load the raw CSV.
    2. Validate schema (ensuring required columns exist).
    3. Clean/normalize data if necessary (e.g., strip whitespace).
    4. Save to the final asset location.
    
    Args:
        raw_path: Path to the raw CSV file (data/raw/reference_substructures_raw.csv).
        output_path: Path for the final asset (data/assets/reference_substructures.csv).
        logger: Logger instance.
    """
    logger.info(f"Starting ingestion from {raw_path}")
    
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw file not found at {raw_path}. "
                                "Ensure T009a (download) and T009b (verify) are completed first.")
    
    # 1. Load raw data
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to read raw CSV: {e}")
        raise
    
    logger.info(f"Loaded {len(df)} rows from raw file.")
    
    # 2. Define expected schema based on typical chemical substructure data
    # Assuming the raw file contains 'substructure', 'smiles', 'description' or similar.
    # We will be generic: check for at least one column named 'smiles' or 'substructure'.
    # If the file has generic columns, we ensure we have a canonical set.
    # Based on T009a source (HuggingFace chembench/reactive_substructures), 
    # expected columns often include 'smiles', 'name', 'reactivity_class'.
    # We will validate that the dataframe is not empty and has a 'smiles' column 
    # if present, or at least one column.
    
    # Strict validation: We expect a 'smiles' column for molecular reactivity tasks.
    # If the raw data doesn't have it, we fail loudly.
    if 'smiles' not in df.columns:
        # Check if it might be named differently
        possible_smiles_cols = [c for c in df.columns if 'smile' in c.lower()]
        if possible_smiles_cols:
            logger.warning(f"Column 'smiles' not found. Using '{possible_smiles_cols[0]}' as smiles source.")
            df.rename(columns={possible_smiles_cols[0]: 'smiles'}, inplace=True)
        else:
            raise ValueError("Schema validation failed: No 'smiles' column found in the raw dataset.")
    
    # 3. Data Cleaning
    # Strip whitespace from string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Remove rows with empty SMILES
    initial_count = len(df)
    df = df[df['smiles'].notna() & (df['smiles'] != '')]
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with invalid/empty SMILES.")
    
    # 4. Save to asset path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    # 5. Verify output checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"Ingestion complete. Output saved to {output_path}")
    logger.info(f"Output SHA-256: {checksum}")

def main():
    """Main entry point for the ingestion task."""
    logger = setup_script_logging()
    config = get_config()
    
    # Define paths relative to project root
    raw_path = os.path.join('data', 'raw', 'reference_substructures_raw.csv')
    output_path = os.path.join('data', 'assets', 'reference_substructures.csv')
    
    try:
        # Ensure directories exist
        ensure_directories()
        
        # Perform ingestion
        ingest_reference_substructures(raw_path, output_path, logger)
        
        logger.info("Task T009c completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
