"""
Validation module for dataset size and integrity checks.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetSizeError(Exception):
    """Raised when the dataset size falls below the minimum threshold."""
    pass

def validate_dataset_size(df: pd.DataFrame, min_size: int = 500, source: str = "dataset") -> bool:
    """
    Validate that the dataset size is above the minimum threshold.
    
    Args:
        df: The dataframe to validate.
        min_size: Minimum required number of rows.
        source: Description of the data source for error messages.
    
    Returns:
        True if valid, raises DatasetSizeError if not.
    """
    size = len(df)
    logger.info(f"Validating {source} size: {size} rows (min: {min_size})")
    
    if size < min_size:
        raise DatasetSizeError(
            f"Dataset size {size} is below minimum threshold of {min_size} for {source}."
        )
    
    return True

def main():
    """Entry point for validation module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate dataset size.')
    parser.add_argument('--input', type=str, required=True, help='Input CSV/Parquet')
    parser.add_argument('--min-size', type=int, default=500, help='Minimum dataset size')
    
    args = parser.parse_args()
    
    # Load data
    if args.input.endswith('.parquet'):
        df = pd.read_parquet(args.input)
    else:
        df = pd.read_csv(args.input)
    
    try:
        validate_dataset_size(df, min_size=args.min_size)
        logger.info("Validation passed.")
    except DatasetSizeError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()