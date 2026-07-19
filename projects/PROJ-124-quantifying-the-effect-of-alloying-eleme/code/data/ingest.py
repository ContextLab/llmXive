"""
Data ingestion and normalization module.

This module implements T013: Parses the raw CSV downloaded by T012,
normalizes elemental fractions to sum to 1.0 (± 0.01 tolerance),
and logs warnings for unknown elements or normalization failures.
"""
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np

from config.environment import get_environment_config
from utils.logger import get_logger
from config.elements import get_abundant_elements_set

logger = get_logger("data.ingest")

def normalize_composition(row: pd.Series, element_columns: List[str]) -> float:
    """
    Calculate the sum of elemental fractions for a single row.
    
    Args:
        row: A row from the dataframe.
        element_columns: List of column names representing elemental fractions.
        
    Returns:
        The sum of fractions (normalization factor).
    """
    total = row[element_columns].sum()
    return float(total)

def ingest_and_normalize():
    """
    Reads the raw CSV, normalizes elemental fractions, and saves to data/processed/features.csv.
    Also logs warnings for unknown elements and rows that do not sum to 1.0 within tolerance.
    
    Requirements:
    - Input: data/raw/gfa_dataset.csv (produced by T012)
    - Output: data/processed/features.csv
    - Behavior: Normalize columns to sum to 1.0. Log warnings for unknown elements.
    """
    config = get_environment_config()
    raw_path = Path(config.raw_data_dir) / "gfa_dataset.csv"
    processed_path = Path(config.processed_data_dir) / "features.csv"
    
    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {raw_path}. "
            "Run code/data/download.py (T012) first to fetch the real data."
        )

    logger.info(f"Loading raw dataset from {raw_path}")
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to read CSV at {raw_path}: {e}")
        raise

    if df.empty:
        raise ValueError(f"Raw dataset at {raw_path} is empty.")

    # Identify composition columns (elemental fractions)
    # Heuristic: Select numeric columns that are not the target variable.
    # The target is typically 'log10_Rc' or 'Rc'.
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    target_candidates = ['log10_Rc', 'Rc', 'target', 'GFA', 'composition_id']
    
    # Filter out target candidates to isolate element columns
    element_cols = [c for c in numeric_cols if c not in target_candidates]
    
    if not element_cols:
        # Fallback: If no numeric columns found excluding targets, check if all numeric cols are elements
        # but maybe named differently. If still empty, fail.
        raise ValueError(
            "No element columns found in the dataset. "
            "Expected numeric columns representing elemental fractions, excluding target variables."
        )

    logger.info(f"Identified {len(element_cols)} element columns: {element_cols[:10]}{'...' if len(element_cols) > 10 else ''}")

    # Check for unknown elements (columns that are not in the known abundant list)
    known_elements = get_abundant_elements_set()
    unknown_elements = [col for col in element_cols if col not in known_elements]
    
    if unknown_elements:
        logger.warning(
            f"Found {len(unknown_elements)} unknown elements in dataset columns: {unknown_elements}. "
            "These will be processed but may not be in the training distribution later."
        )

    # Calculate sums for normalization
    sums = df[element_cols].sum(axis=1)
    
    # Define tolerance
    tolerance = 0.01
    
    # Identify rows that do not sum to 1.0 within tolerance
    # Note: We allow rows to be normalized even if they are outside tolerance,
    # but we log a warning as per T013 requirements.
    bad_rows_mask = abs(sums - 1.0) > tolerance
    bad_rows_count = bad_rows_mask.sum()
    
    if bad_rows_count > 0:
        logger.warning(
            f"Found {bad_rows_count} rows where elemental fractions do not sum to 1.0 ± {tolerance}. "
            "These rows will be normalized to sum to 1.0 anyway."
        )
    
    # Identify rows with zero sum (to avoid division by zero)
    zero_sum_mask = sums == 0
    zero_sum_count = zero_sum_mask.sum()
    
    if zero_sum_count > 0:
        logger.error(
            f"Found {zero_sum_count} rows where elemental fractions sum to 0. "
            "These rows cannot be normalized and will be dropped."
        )
        # Drop rows with zero sum
        df = df[~zero_sum_mask]
        sums = sums[~zero_sum_mask]
        element_cols_subset = element_cols
        
        # Re-evaluate bad rows after dropping zero-sum rows
        sums = df[element_cols].sum(axis=1)
        bad_rows_mask = abs(sums - 1.0) > tolerance
        if bad_rows_mask.sum() > 0:
             logger.warning(
                 f"After dropping zero-sum rows, {bad_rows_mask.sum()} rows still do not sum to 1.0 ± {tolerance}."
             )

    # Apply normalization: divide each element column by the row sum
    # Use div with axis=0 to broadcast division by row sums
    df[element_cols] = df[element_cols].div(sums, axis=0)
    
    # Ensure no NaNs introduced (should be covered by zero-sum drop, but safe-guard)
    df[element_cols] = df[element_cols].fillna(0)
    
    # Verify normalization (sanity check)
    final_sums = df[element_cols].sum(axis=1)
    if not np.allclose(final_sums, 1.0, atol=tolerance):
        logger.warning("Normalization verification failed: some rows still do not sum to 1.0.")

    # Ensure output directory exists
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to processed directory
    df.to_csv(processed_path, index=False)
    logger.info(
        f"Ingested and normalized dataset saved to {processed_path} "
        f"({len(df)} rows, {len(element_cols)} element columns)."
    )

def main():
    """Main entry point for the ingestion script."""
    ingest_and_normalize()

if __name__ == "__main__":
    main()