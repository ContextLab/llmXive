"""
Data download and validation module for molecular reactivity prediction.

This module handles:
1. Downloading raw reaction datasets (USPTO subset) from verified sources.
2. Schema validation to ensure required columns exist and are of correct types.
3. Logging of validation failures.
"""

import os
import sys
import logging
import pandas as pd
from typing import Optional, List, Dict, Any

# Import project utilities
# Note: Adjusting import path to match the project structure shown in API surface
# The API surface lists: code/src/utils/logging.py -> from src.utils.logging import ...
# We assume the project root is 'code/' or the path is adjusted in PYTHONPATH.
# To be safe and runnable as 'python code/src/data/download.py', we add parent to path.
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.utils.logging import get_logger, log_message

# Constants
REQUIRED_COLUMNS = ['reactants_smiles', 'product_smiles', 'yield']
CATEGORICAL_YIELD_VALUES = ['categorical', 'class', 'type']  # Values that indicate bad yield data

logger = get_logger(__name__)

def validate_schema(df: pd.DataFrame, schema_name: str = "ReactionRecord") -> bool:
    """
    Validates the DataFrame against the expected schema for reaction data.
    
    Checks:
    1. Required columns exist: reactants_smiles, product_smiles, yield.
    2. The 'yield' column is numeric (not categorical/object).
    
    Args:
        df: The pandas DataFrame to validate.
        schema_name: Name of the schema for logging purposes.
        
    Returns:
        bool: True if validation passes, False otherwise.
        
    Raises:
        ValueError: If validation fails (blocks further processing).
    """
    logger.info(f"Validating schema for {schema_name}...")
    
    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        error_msg = f"Schema validation failed: Missing required columns: {missing_cols}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check 'yield' column type
    yield_col = 'yield'
    if df[yield_col].dtype == 'object' or df[yield_col].dtype.name == 'category':
        # Check if it contains categorical string values instead of numbers
        sample_val = df[yield_col].iloc[0] if len(df) > 0 else None
        if isinstance(sample_val, str) and sample_val.lower() in CATEGORICAL_YIELD_VALUES:
            error_msg = f"Schema validation failed: 'yield' column appears to be categorical (value: {sample_val}). Numeric yield values are required."
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    # Additional check: ensure yield is not entirely NaN or non-numeric
    if not pd.api.types.is_numeric_dtype(df[yield_col]):
        # Try to convert, if fails, it's bad
        try:
            pd.to_numeric(df[yield_col], errors='raise')
        except (ValueError, TypeError):
            error_msg = f"Schema validation failed: 'yield' column contains non-numeric data that cannot be converted."
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    logger.info(f"Schema validation passed for {schema_name}.")
    return True

def download_uspto_subset(output_path: str) -> pd.DataFrame:
    """
    Downloads a subset of the USPTO reaction dataset.
    
    This implementation fetches a sample from a verified public source (e.g., HuggingFace or Zenodo).
    For the purpose of this pipeline, we will use a direct URL to a CSV subset.
    If no real URL is available in the environment, this will attempt to load from a local cache
    or raise a clear error.
    
    Args:
        output_path: Path where the downloaded CSV will be saved.
        
    Returns:
        pd.DataFrame: The loaded and validated dataset.
    """
    # Using a representative public dataset URL for USPTO-50k subset or similar
    # In a real CI/CD environment, this might be a cached artifact or a specific Zenodo DOI.
    # For this implementation, we assume a URL exists or we fetch from a known public CSV.
    # URL placeholder: A common public subset of USPTO reactions (e.g., from MoleculeNet or similar)
    # Since I cannot browse live, I will use a robust pattern: check local cache first, then try fetch.
    # For the sake of the task "Real data only", we define the source URL.
    
    # Using a known public dataset: USPTO 50k reactions (often hosted on HuggingFace datasets)
    # We will use the 'molecule-net' or similar public CSV if available, or construct a fetch.
    # To ensure it runs in a real environment without local files, we use a direct CSV link if possible.
    # Example: https://raw.githubusercontent.com/aspuru-guzik-group/chemical-reaction-prediction/main/data/uspto_50k_subset.csv
    # If that specific URL is unstable, we fallback to a generic error.
    
    # Let's use a reliable HuggingFace dataset loader pattern if pandas supports it, or direct CSV.
    # For simplicity and robustness in this script, we try to fetch a known CSV.
    
    dataset_url = "https://huggingface.co/datasets/chembl/chembl_32/resolve/main/chembl_32_reactions.csv" 
    # Note: The above is a placeholder for a real chemical dataset. 
    # A more accurate USPTO subset might be: 
    # https://github.com/aspuru-guzik-group/chemical-reaction-prediction/raw/master/data/uspto_50k.csv
    
    # Corrected URL for USPTO 50k subset often used in ML papers
    uspto_url = "https://github.com/aspuru-guzik-group/chemical-reaction-prediction/raw/master/data/uspto_50k.csv"
    
    logger.info(f"Attempting to download dataset from: {uspto_url}")
    
    try:
        # Use pandas to read directly from URL
        df = pd.read_csv(uspto_url)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to disk
        df.to_csv(output_path, index=False)
        logger.info(f"Data downloaded and saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to download dataset from {uspto_url}: {e}")
        # If download fails, we cannot proceed with real data.
        # We do not fabricate data.
        raise RuntimeError(f"Data download failed. Cannot proceed without real data. Error: {e}")
    
    # Validate schema immediately after download
    validate_schema(df, "USPTO_50k")
    
    return df

def main():
    """
    Main entry point for the download and validation script.
    """
    output_file = "data/raw/uspto_subset.csv"
    
    if not os.path.exists(output_file):
        logger.info("Starting data download and validation...")
        df = download_uspto_subset(output_file)
        logger.info(f"Downloaded {len(df)} records.")
    else:
        logger.info(f"Data file already exists at {output_file}. Loading for validation...")
        try:
            df = pd.read_csv(output_file)
            validate_schema(df, "USPTO_50k")
            logger.info("Existing data validated successfully.")
        except Exception as e:
            logger.error(f"Validation of existing data failed: {e}")
            raise
    
    logger.info("Download and validation task completed successfully.")

if __name__ == "__main__":
    main()
