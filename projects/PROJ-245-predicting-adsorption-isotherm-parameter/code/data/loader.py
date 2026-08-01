"""
Data Loader Module for Adsorption Isotherm Parameter Prediction.

This module handles the fetching, loading, and validation of real experimental data
from the NIST/MOF-1000 dataset. It strictly enforces the "Real Data Only" policy:
if the fetch fails, it raises a DataFetchError and terminates. No synthetic fallbacks are permitted.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd

# Import from sibling modules using the defined API surface
from data.download import attempt_nist_fetch, write_verification_log
from data.validate_schema import load_schema, validate_dataframe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception raised when real data fetching fails."""
    pass

def ensure_directories(base_dir: str) -> None:
    """Create necessary directories for raw and processed data."""
    raw_dir = Path(base_dir) / "raw"
    processed_dir = Path(base_dir) / "processed"
    audit_dir = Path(base_dir) / "audit"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Ensured directories exist: {raw_dir}, {processed_dir}, {audit_dir}")

def load_raw_data(base_dir: str) -> pd.DataFrame:
    """
    Load raw data from the local cache if it exists, otherwise attempt to fetch it.
    
    Args:
        base_dir: The base directory containing the 'raw' subdirectory.
        
    Returns:
        A pandas DataFrame containing the raw data.
        
    Raises:
        DataFetchError: If the data cannot be fetched and no valid local copy exists.
    """
    raw_dir = Path(base_dir) / "raw"
    data_file = raw_dir / "nist_mof1000.csv"
    
    if data_file.exists():
        logger.info(f"Loading existing raw data from {data_file}")
        try:
            df = pd.read_csv(data_file)
            logger.info(f"Successfully loaded {len(df)} rows from local cache.")
            return df
        except Exception as e:
            logger.error(f"Failed to read local cache: {e}. Attempting fetch.")
    
    # Attempt to fetch real data
    logger.info("Attempting to fetch real data from NIST/MOF-1000...")
    fetch_success = attempt_nist_fetch(str(raw_dir))
    
    if not fetch_success:
        # CRITICAL: No synthetic fallback. Raise error and write failure log.
        error_msg = "Real data fetch from NIST/MOF-1000 failed. No synthetic fallback permitted."
        logger.error(error_msg)
        
        # Write verification log indicating failure
        log_entry = {
            "status": "REAL_DATA_FETCH_FAILED",
            "rationale": "The attempt to fetch real experimental data from the NIST/MOF-1000 source failed. "
                         "Per project constraints, synthetic data generation is strictly prohibited. "
                         "The pipeline must terminate to prevent fabrication of results.",
            "timestamp": str(pd.Timestamp.now()),
            "source": "NIST/MOF-1000",
            "file_path": str(data_file)
        }
        
        write_verification_log(str(raw_dir), log_entry)
        raise DataFetchError(error_msg)
    
    # If fetch was successful, reload the file
    if not data_file.exists():
        raise DataFetchError("Fetch reported success but file does not exist.")
        
    logger.info(f"Loading fetched data from {data_file}")
    df = pd.read_csv(data_file)
    logger.info(f"Successfully loaded {len(df)} rows from fetched data.")
    return df

def validate_loaded_data(df: pd.DataFrame, schema_path: str = "contracts/dataset.schema.yaml") -> Tuple[bool, Optional[str]]:
    """
    Validate the loaded DataFrame against the defined schema.
    
    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema YAML file.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        schema = load_schema(schema_path)
        is_valid, errors = validate_dataframe(df, schema)
        
        if not is_valid:
            error_details = "; ".join(errors) if errors else "Schema validation failed."
            logger.error(f"Data validation failed: {error_details}")
            return False, error_details
        
        logger.info("Data validation passed against schema.")
        return True, None
        
    except Exception as e:
        logger.error(f"Error during validation process: {e}")
        return False, str(e)

def load_and_preprocess_data(base_dir: str) -> pd.DataFrame:
    """
    Orchestrate the loading and initial preprocessing of the dataset.
    
    This function:
    1. Ensures directories exist.
    2. Loads raw data (fetching if necessary).
    3. Validates the data against the schema.
    4. Performs basic cleaning (dropping obvious null rows if allowed by schema).
    
    Args:
        base_dir: The base directory for data storage.
        
    Returns:
        A cleaned and validated pandas DataFrame.
        
    Raises:
        DataFetchError: If data fetching fails.
        ValueError: If data validation fails.
    """
    ensure_directories(base_dir)
    
    # Load raw data
    df = load_raw_data(base_dir)
    
    # Validate
    is_valid, error_msg = validate_loaded_data(df)
    if not is_valid:
        raise ValueError(f"Data validation failed: {error_msg}")
    
    # Basic preprocessing: Drop rows with completely empty index if any
    initial_count = len(df)
    df = df.dropna(how='all')
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.info(f"Dropped {dropped} completely empty rows.")
        
    return df

def main():
    """
    Entry point for the loader script.
    Runs the full fetch, load, and validate pipeline.
    Writes the processed output to data/processed/curated_data.csv if successful.
    """
    # Determine base directory
    # If running as script, assume project root is parent of 'code'
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    data_dir = project_root / "data"
    
    logger.info(f"Starting data loading pipeline. Base dir: {data_dir}")
    
    try:
        # Load and validate
        df = load_and_preprocess_data(str(data_dir))
        
        # Save the validated dataset
        output_path = data_dir / "processed" / "curated_data.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved validated data to {output_path}")
        
        # Write a success log
        log_entry = {
            "status": "REAL_DATA_FETCH_SUCCESS",
            "rows_loaded": len(df),
            "timestamp": str(pd.Timestamp.now()),
            "output_file": str(output_path)
        }
        write_verification_log(str(data_dir), log_entry)
        
        return 0
        
    except DataFetchError as e:
        logger.critical(f"Pipeline failed due to data fetch error: {e}")
        return 1
    except ValueError as e:
        logger.critical(f"Pipeline failed due to validation error: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error in loader: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
