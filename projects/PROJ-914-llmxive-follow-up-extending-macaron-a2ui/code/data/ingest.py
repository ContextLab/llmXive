"""
Data Ingestion Module for Macaron-A2UI Project.

Handles loading raw data from Hugging Face datasets with strict
adherence to Data Hygiene principles: no synthetic fallbacks.
"""
import os
import sys
import argparse
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
from datasets import load_dataset

from config import get_raw_data_path, ensure_dirs
from utils.logging import get_experiment_logger, log_error, log_info

# Constants
DATASET_ID = "macaron-data/a2ui-bench"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

logger = get_experiment_logger("ingest")

def load_dataset_from_hf(
    dataset_id: str = DATASET_ID,
    streaming: bool = True,
    sample_size: Optional[int] = None
) -> pd.DataFrame:
    """
    Load dataset from Hugging Face Hub.
    
    Args:
        dataset_id: The Hugging Face dataset identifier (namespace/name).
        streaming: If True, stream the dataset to save memory.
        sample_size: Optional number of rows to sample if streaming.
        
    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        RuntimeError: If the dataset cannot be loaded from a real source.
        FileNotFoundError: If the dataset ID is invalid or inaccessible.
    """
    logger.info(f"Attempting to load dataset: {dataset_id} (streaming={streaming})...")
    
    start_time = time.time()
    
    try:
        # Attempt to load the dataset with strict error handling
        # No trust_remote_code as per modern HF standards
        ds = load_dataset(
            dataset_id,
            streaming=streaming,
            trust_remote_code=False  # Explicitly disabled per HF 3.0+ requirements
        )
        
        # Determine which split to use (prefer 'train' or first available)
        split_name = 'train' if 'train' in ds else list(ds.keys())[0]
        logger.info(f"Using split: {split_name}")
        
        if streaming:
            # Convert iterator to list if sample_size is specified
            if sample_size:
                logger.info(f"Sampling {sample_size} rows from stream...")
                # Use islice to get exactly sample_size rows
                from itertools import islice
                data_iter = islice(ds[split_name], sample_size)
                df = pd.DataFrame(list(data_iter))
            else:
                # Materialize entire stream (risky for large datasets, but explicit)
                logger.warning("Streaming without sample_size will materialize entire dataset.")
                df = pd.DataFrame(list(ds[split_name]))
        else:
            # Load full dataset into memory
            df = ds[split_name].to_pandas()
            if sample_size and sample_size < len(df):
                logger.info(f"Sampling {sample_size} rows from loaded dataset...")
                df = df.head(sample_size)
        
        elapsed = time.time() - start_time
        logger.info(f"Successfully loaded {len(df)} rows in {elapsed:.2f}s")
        
        return df
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"CRITICAL: Failed to load real dataset from {dataset_id}. Error: {error_msg}")
        
        # Explicitly check for common failure modes and raise clear errors
        if "doesn't exist" in error_msg or "not found" in error_msg:
            raise FileNotFoundError(
                f"Dataset '{dataset_id}' does not exist on the Hub or is inaccessible. "
                "Per Data Hygiene Principle, no synthetic fallback is allowed. "
                "Please verify the dataset ID and network connectivity."
            ) from e
        elif "trust_remote_code" in error_msg:
            raise RuntimeError(
                f"Dataset '{dataset_id}' requires legacy loading scripts which are no longer supported. "
                "Per Data Hygiene Principle, no synthetic fallback is allowed. "
                "The dataset must be converted to a standard format (Parquet/Arrow) by the author."
            ) from e
        else:
            raise RuntimeError(
                f"Failed to fetch real data from {dataset_id}. "
                "Per Data Hygiene Principle, no synthetic fallback is allowed. "
                "Check network connection and dataset availability."
            ) from e

def validate_dataframe(df: pd.DataFrame, required_columns: list) -> bool:
    """
    Validate that the DataFrame has the required columns and non-null values.
    
    Args:
        df: The DataFrame to validate.
        required_columns: List of column names that must exist.
        
    Returns:
        bool: True if valid, raises ValueError otherwise.
    """
    if df.empty:
        raise ValueError("Loaded dataset is empty.")
        
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    # Check for critical nulls in key fields (query/intent)
    if 'query' in df.columns and df['query'].isnull().any():
        raise ValueError("Dataset contains null values in 'query' column.")
        
    logger.info(f"Validation passed: {df.shape[0]} rows, {df.shape[1]} columns")
    return True

def save_raw_csv(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Save the raw dataset to a CSV file.
    
    Args:
        df: The DataFrame to save.
        output_path: Optional custom path. Defaults to config.
        
    Returns:
        str: The path to the saved file.
    """
    if output_path is None:
        output_path = str(get_raw_data_path())
        
    output_file = Path(output_path)
    ensure_dirs()
    
    # Ensure parent directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_file, index=False)
    logger.info(f"Saved raw data to {output_file}")
    
    # Compute hash for versioning
    with open(output_file, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    logger.info(f"Data hash: {file_hash}")
    
    return str(output_file)

def main():
    """CLI entry point for data ingestion."""
    parser = argparse.ArgumentParser(description="Ingest Macaron-A2UI dataset")
    parser.add_argument(
        "--annotate",
        action="store_true",
        help="Prepare data for annotation (sample N=500)"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500,
        help="Number of rows to sample (default: 500)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output path"
    )
    
    args = parser.parse_args()
    
    try:
        # Load dataset
        df = load_dataset_from_hf(
            dataset_id=DATASET_ID,
            streaming=True,
            sample_size=args.sample_size if args.annotate else None
        )
        
        # Validate
        required_cols = ['query'] # Minimum requirement
        validate_dataframe(df, required_cols)
        
        # Save
        output_path = save_raw_csv(df, args.output)
        
        logger.info(f"Ingestion complete. Output: {output_path}")
        
        if args.annotate:
            logger.info(f"Ready for annotation with {len(df)} rows.")
            
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        log_error(f"Ingestion failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error during ingestion: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()