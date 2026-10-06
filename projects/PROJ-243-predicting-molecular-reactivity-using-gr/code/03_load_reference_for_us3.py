"""
Load curated reference set of known reactive substructures from data/assets/reference_substructures.csv.

This script implements Task T029: Load curated reference set of known reactive substructures.
It verifies the file exists, loads the data, validates the schema, and logs the successful
utilization of the reference set for downstream attribution analysis.

Dependencies:
  - T010c: Must have produced data/assets/reference_substructures.csv
  - T010c-utilize: This script is the implementation of that utilization step
"""

import os
import sys
import logging
import pandas as pd
from typing import Optional

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config, ensure_directories

def setup_script_logging():
    """Configure logging for this script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('artifacts/logs/t029_reference_loader.log')
        ]
    )
    return logging.getLogger(__name__)

def load_reference_substructures(logger: logging.Logger, config: dict) -> Optional[pd.DataFrame]:
    """
    Load the curated reference substructures dataset.
    
    Args:
        logger: Logger instance for recording operations
        config: Configuration dictionary containing file paths
        
    Returns:
        pandas DataFrame with reference substructures, or None if loading fails
        
    Raises:
        FileNotFoundError: If the reference file does not exist
        ValueError: If the schema validation fails
    """
    reference_path = config.get('paths', {}).get('reference_substructures_assets')
    
    if not reference_path:
        # Fallback to default path if not in config
        reference_path = os.path.join(config.get('paths', {}).get('assets', 'data/assets'), 'reference_substructures.csv')
    
    logger.info(f"Attempting to load reference substructures from: {reference_path}")
    
    # Check if file exists
    if not os.path.exists(reference_path):
        error_msg = f"Reference substructures file not found at: {reference_path}. " \
                   f"Ensure T010c has successfully produced this file."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Check if file is non-empty
    if os.path.getsize(reference_path) == 0:
        error_msg = f"Reference substructures file is empty at: {reference_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Load the CSV file
        df = pd.read_csv(reference_path)
        logger.info(f"Successfully loaded {len(df)} rows from {reference_path}")
        
        # Validate required columns
        required_columns = {'smiles', 'source_doi', 'description'}
        available_columns = set(df.columns)
        missing_columns = required_columns - available_columns
        
        if missing_columns:
            error_msg = f"Missing required columns in reference substructures: {missing_columns}. " \
                       f"Available columns: {list(df.columns)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate data quality
        if df['smiles'].isna().any():
            logger.warning(f"Found {df['smiles'].isna().sum()} rows with missing SMILES values")
        
        if df['source_doi'].isna().any():
            logger.warning(f"Found {df['source_doi'].isna().sum()} rows with missing source DOI")
        
        if df['description'].isna().any():
            logger.warning(f"Found {df['description'].isna().sum()} rows with missing descriptions")
        
        # Remove rows with missing critical data
        initial_count = len(df)
        df = df.dropna(subset=['smiles'])
        removed_count = initial_count - len(df)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} rows with missing SMILES values")
        
        if len(df) == 0:
            error_msg = "No valid reference substructures remain after filtering. " \
                       "The dataset must contain at least one valid entry."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Reference substructures loaded successfully: {len(df)} valid entries")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Sample SMILES: {df['smiles'].iloc[0] if len(df) > 0 else 'N/A'}")
        
        return df
        
    except pd.errors.EmptyDataError:
        error_msg = f"Reference substructures file is empty or malformed: {reference_path}"
        logger.error(error_msg)
        raise
    except pd.errors.ParserError as e:
        error_msg = f"Failed to parse reference substructures CSV: {e}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Unexpected error loading reference substructures: {e}"
        logger.error(error_msg)
        raise

def main():
    """Main entry point for the reference substructures loader."""
    logger = setup_script_logging()
    logger.info("=" * 60)
    logger.info("Starting T029: Load curated reference set of known reactive substructures")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        config = get_config()
        ensure_directories(config)
        
        # Load the reference substructures
        reference_df = load_reference_substructures(logger, config)
        
        if reference_df is not None:
            logger.info("T029 COMPLETED: Reference substructures loaded and validated successfully")
            logger.info(f"Final dataset contains {len(reference_df)} valid reactive substructures")
            return 0
        else:
            logger.error("T029 FAILED: Failed to load reference substructures")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"T029 FAILED: {e}")
        return 1
    except ValueError as e:
        logger.error(f"T029 FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"T029 FAILED: Unexpected error - {e}")
        return 1
    
    finally:
        logger.info("=" * 60)
        logger.info("T029 Execution Complete")
        logger.info("=" * 60)

if __name__ == "__main__":
    sys.exit(main())