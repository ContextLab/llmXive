"""
ID Generator Module for llmXive Pipeline.

This module provides functionality to generate deterministic, unique SHA256
sample IDs by combining cohort information and original sample IDs.
"""

import hashlib
import pandas as pd
import logging
import argparse
from typing import List, Optional, Tuple

from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def generate_sample_id(cohort: str, original_id: str) -> str:
    """
    Generate a deterministic SHA256 sample ID from cohort and original_id.

    Args:
        cohort: The cohort name (e.g., 'AGP', 'UKBB').
        original_id: The original sample identifier from the source dataset.

    Returns:
        A 64-character hexadecimal SHA256 hash string.
    """
    if not cohort or not original_id:
        raise ValueError("Both 'cohort' and 'original_id' must be non-empty strings.")

    # Construct a deterministic string for hashing
    # Format: "cohort:original_id" ensures uniqueness and readability in hash input
    raw_string = f"{cohort}:{original_id}"

    # Encode to bytes and compute SHA256
    hash_object = hashlib.sha256(raw_string.encode('utf-8'))
    return hash_object.hexdigest()


def generate_sample_ids_dataframe(df: pd.DataFrame, 
                                  cohort_col: str = 'cohort', 
                                  original_id_col: str = 'original_id', 
                                  target_col: str = 'sample_id') -> pd.DataFrame:
    """
    Add a new column to a DataFrame containing generated SHA256 sample IDs.

    Args:
        df: The input DataFrame containing cohort and original_id columns.
        cohort_col: Name of the column containing cohort names.
        original_id_col: Name of the column containing original sample IDs.
        target_col: Name of the new column to create for the generated IDs.

    Returns:
        The DataFrame with the new 'sample_id' column added.
    
    Raises:
        ValueError: If required columns are missing or contain nulls.
    """
    if cohort_col not in df.columns:
        raise ValueError(f"Column '{cohort_col}' not found in DataFrame.")
    if original_id_col not in df.columns:
        raise ValueError(f"Column '{original_id_col}' not found in DataFrame.")

    if df[cohort_col].isnull().any() or df[original_id_col].isnull().any():
        raise ValueError("Cohort and original_id columns must not contain null values.")

    logger.info(f"Generating sample IDs for {len(df)} rows using columns '{cohort_col}' and '{original_id_col}'.")

    df[target_col] = df.apply(
        lambda row: generate_sample_id(str(row[cohort_col]), str(row[original_id_col])), 
        axis=1
    )

    logger.info(f"Successfully generated {len(df)} unique sample IDs.")
    return df


def main() -> None:
    """
    Command-line entry point for generating sample IDs from a CSV/TSV file.
    
    Usage:
        python -m src.preprocessing.id_generator --input data/raw/input.tsv --output data/processed/ids.tsv
    """
    parser = argparse.ArgumentParser(description="Generate SHA256 sample IDs for a dataset.")
    parser.add_argument('--input', '-i', required=True, help='Path to input CSV/TSV file.')
    parser.add_argument('--output', '-o', required=True, help='Path to output CSV/TSV file.')
    parser.add_argument('--cohort-col', default='cohort', help='Name of the cohort column.')
    parser.add_argument('--original-id-col', default='original_id', help='Name of the original ID column.')
    parser.add_argument('--target-col', default='sample_id', help='Name of the output ID column.')
    parser.add_argument('--sep', default='\\t', help='Delimiter for input/output files (default: tab).')
    
    args = parser.parse_args()

    try:
        # Determine delimiter based on file extension if not specified, or use args.sep
        sep = args.sep
        if sep == '\\t':
            sep = '\t'
        
        logger.info(f"Loading data from {args.input}")
        df = pd.read_csv(args.input, sep=sep)
        
        logger.info(f"Input shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")

        df_processed = generate_sample_ids_dataframe(
            df, 
            cohort_col=args.cohort_col, 
            original_id_col=args.original_id_col, 
            target_col=args.target_col
        )

        logger.info(f"Saving processed data to {args.output}")
        df_processed.to_csv(args.output, sep=sep, index=False)
        
        logger.info("ID generation completed successfully.")
        
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise


if __name__ == "__main__":
    main()