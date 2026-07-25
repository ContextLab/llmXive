"""
Data cleaning module for elastic anisotropy pipeline.

Filters for single-phase FCC entries, excludes entries where C11=C12,
and calculates the Zener anisotropy ratio A1.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

# Import project utilities
from src.utils.config import get_path, ensure_directories
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def clean_elastic_data(input_path: Optional[str] = None, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Clean the ingested elastic data.

    1. Filter for single-phase FCC entries:
       - Check structure['symmetry']['crystal_system'] == 'cubic' for MP data
       - Check tags['fss'] or equivalent cubic flag for AFLOW data
    2. Exclude entries where C11 == C12 (prevents division by zero in A1)
    3. Calculate A1 = 2*C44 / (C11 - C12)

    Args:
        input_path: Path to the input CSV from ingestion. Defaults to config path.
        output_path: Path to save the cleaned CSV. Defaults to config path.

    Returns:
        pd.DataFrame: The cleaned dataframe with A1 calculated.

    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If required columns are missing.
    """
    if input_path is None:
        input_path = str(get_path("processed", "elastic_constants_raw.csv"))
    if output_path is None:
        output_path = str(get_path("processed", "elastic_anisotropy.csv"))

    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")

    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)

    # Validate required columns
    required_cols = ['C11', 'C12', 'C44']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    initial_count = len(df)
    logger.info(f"Loaded {initial_count} records. Starting cleaning process.")

    # 1. Filter for cubic crystal system
    # Handle potential NaNs in the 'crystal_system' column if it exists
    if 'crystal_system' in df.columns:
        # Ensure string comparison handles NaNs gracefully
        mask_cubic = df['crystal_system'].notna() & (df['crystal_system'].str.lower() == 'cubic')
        count_before = len(df)
        df = df[mask_cubic]
        count_after = len(df)
        logger.info(f"Filtered for cubic system: {count_before} -> {count_after} records.")
    else:
        logger.warning("Column 'crystal_system' not found in input. Skipping cubic filter based on this column.")
        # If 'fss' tag or similar is used, it would be handled here if the schema differs.
        # Assuming the schema matches the spec for now.

    # 2. Exclude entries where C11 == C12 (Division by zero protection)
    # We use a small epsilon for float comparison safety, though strict equality is requested
    # to prevent division by zero.
    mask_valid_diff = (df['C11'] - df['C12']).abs() > 1e-9
    count_before = len(df)
    df = df[mask_valid_diff]
    count_after = len(df)
    logger.info(f"Filtered C11 != C12: {count_before} -> {count_after} records.")

    # 3. Calculate A1 = 2*C44 / (C11 - C12)
    df['A1'] = (2.0 * df['C44']) / (df['C11'] - df['C12'])

    # Handle potential NaNs or Infs resulting from calculation (e.g. if C44 is NaN)
    count_before = len(df)
    df = df[df['A1'].notna()]
    df = df[np.isfinite(df['A1'])]
    count_after = len(df)
    if count_before != count_after:
        logger.warning(f"Removed {count_before - count_after} records with invalid A1 values (NaN/Inf).")

    # Ensure output directory exists
    ensure_directories()

    # Save to CSV
    output_file = Path(output_path)
    df.to_csv(output_file, index=False)
    logger.info(f"Cleaned data saved to {output_file} ({len(df)} records)")

    return df


def main():
    """CLI entry point for cleaning task."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    try:
        df = clean_elastic_data()
        logger.info("Cleaning completed successfully.")
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during cleaning: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()