import os
import pandas as pd
from typing import Optional
from pathlib import Path

# Import existing utilities from the project
from utils.logging import get_logger
from data.models import create_subjects_from_dataframe
from data.synthetic_generator import generate_synthetic_dataset

logger = get_logger(__name__)


class DataAccessError(Exception):
    """Raised when data access fails in analysis mode or real data is missing."""
    pass


def load_data(path: str, mode: str) -> pd.DataFrame:
    """
    Load data based on the specified mode and path.

    Args:
        path: Path to the data file (used in analysis mode).
        mode: Either 'analysis' or 'verification'.

    Returns:
        pd.DataFrame: Loaded data.

    Raises:
        DataAccessError: If in analysis mode and real data is missing.
        ValueError: If insufficient data for statistical power (<50 per group).
    """
    logger.info(f"Loading data in '{mode}' mode from path: {path}")

    df = None

    if mode == 'analysis':
        # Analysis mode requires real data
        if not os.path.exists(path):
            raise DataAccessError(f"Data Source Missing: Real data required for Analysis Mode. Path: {path}")
        
        try:
            # Attempt to load the real data file
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            elif path.endswith('.parquet'):
                df = pd.read_parquet(path)
            else:
                # Try generic loading or raise error for unsupported formats
                raise ValueError(f"Unsupported file format for analysis: {path}")
            
            logger.info(f"Successfully loaded real data with {len(df)} rows")
            
        except Exception as e:
            raise DataAccessError(f"Failed to load real data from {path}: {str(e)}")

    elif mode == 'verification':
        # Verification mode uses synthetic data
        logger.info("Generating synthetic dataset for verification mode")
        df = generate_synthetic_dataset()
        logger.info(f"Generated synthetic dataset with {len(df)} rows")
    
    else:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'analysis' or 'verification'.")

    # Mandatory Power Check
    # Ensure sufficient subjects per group for statistical power
    musician_count = len(df[df['group'] == 'musician'])
    non_musician_count = len(df[df['group'] == 'non_musician'])

    if musician_count < 50 or non_musician_count < 50:
        error_msg = f"Insufficient Data for Power: <50 subjects per group (musician: {musician_count}, non_musician: {non_musician_count})"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Data loaded successfully. Musician count: {musician_count}, Non-musician count: {non_musician_count}")
    return df


def main():
    """
    Entry point for the download module to test data loading.
    Usage: python -m code.data.download --mode verification
    """
    import argparse

    parser = argparse.ArgumentParser(description="Load data for analysis or verification.")
    parser.add_argument("--mode", type=str, required=True, choices=["analysis", "verification"],
                        help="Mode: 'analysis' (requires real data) or 'verification' (synthetic)")
    parser.add_argument("--path", type=str, default="data/raw/real_data.csv",
                        help="Path to data file (required for analysis mode)")

    args = parser.parse_args()

    try:
        df = load_data(args.path, args.mode)
        print(f"Successfully loaded {len(df)} records.")
        print(df.head())
    except (DataAccessError, ValueError) as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())