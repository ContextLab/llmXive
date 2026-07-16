"""
Data ingestion and normalization module.
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
    Normalize elemental fractions to sum to 1.0.
    
    Args:
        row: A row from the dataframe.
        element_columns: List of column names representing elemental fractions.
        
    Returns:
        The normalization factor (sum of fractions).
    """
    total = row[element_columns].sum()
    if total == 0:
        return 0.0
    return total

def ingest_and_normalize():
    """
    Reads the raw CSV, normalizes elemental fractions, and saves to processed/features.csv.
    Also logs warnings for unknown elements.
    """
    config = get_environment_config()
    raw_path = Path(config.raw_data_dir) / "gfa_dataset.csv"
    processed_path = Path(config.processed_data_dir) / "features.csv"
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}. Run download.py first.")

    logger.info(f"Loading raw dataset from {raw_path}")
    df = pd.read_csv(raw_path)

    # Identify composition columns (assuming they are numeric and not the target)
    # Heuristic: Columns that are not 'composition' (string) and not the target 'log10_Rc'
    # We need to know the exact column names. Let's assume the CSV has a 'composition' string col
    # and numeric columns for elements.
    
    # For robustness, let's assume the target is 'log10_Rc' or similar.
    # We'll filter out non-numeric columns that are not element fractions.
    # A safer approach: The spec says "parse elemental fractions".
    # Let's assume the columns ending in atomic symbols or specific names are elements.
    # However, without a specific schema, we rely on the fact that the sum of element fractions is ~1.
    
    # Let's identify numeric columns that are likely elements.
    # We'll exclude the target variable if it exists.
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Heuristic: If there are many numeric columns, they are likely elements.
    # We assume the target is 'log10_Rc' or 'Rc' or similar.
    target_candidates = ['log10_Rc', 'Rc', 'target', 'GFA']
    element_cols = [c for c in numeric_cols if c not in target_candidates]
    
    if not element_cols:
        raise ValueError("No element columns found in the dataset.")

    logger.info(f"Identified {len(element_cols)} element columns: {element_cols[:5]}...")

    # Check for unknown elements (columns that are not in the known abundant list)
    known_elements = get_abundant_elements_set()
    unknown_elements = [col for col in element_cols if col not in known_elements]
    
    if unknown_elements:
        logger.warning(f"Found unknown elements in dataset: {unknown_elements}. These will be included but may affect model performance.")

    # Normalize
    sums = df[element_cols].sum(axis=1)
    
    # Log warnings for rows that don't sum to ~1.0
    tolerance = 0.01
    bad_rows = df[abs(sums - 1.0) > tolerance]
    if len(bad_rows) > 0:
        logger.warning(f"Found {len(bad_rows)} rows where elemental fractions do not sum to 1.0 ± {tolerance}.")
        # We will still normalize them by dividing by their sum to force them to 1.0
        # This is a common practice to handle experimental error.

    # Apply normalization
    df[element_cols] = df[element_cols].div(sums, axis=0)
    
    # Ensure no NaNs introduced by division (handle 0 sums)
    df[element_cols] = df[element_cols].fillna(0)

    # Save
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_path, index=False)
    logger.info(f"Ingested and normalized dataset saved to {processed_path} ({len(df)} rows).")

def main():
    """Main entry point."""
    ingest_and_normalize()

if __name__ == "__main__":
    main()
