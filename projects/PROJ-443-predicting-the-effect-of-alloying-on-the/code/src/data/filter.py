"""
Filtering logic for High-Entropy Alloy (HEA) samples.

Retains samples with:
- At least 5 principal elements (composition >= 0.05 or >= 0.01 depending on definition, here >= 0.05 for 'principal')
- Valid Bulk Modulus (non-null, positive)
"""

import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

from src.utils.logging_config import get_logger

# Configuration constants
MIN_PRINCIPAL_ELEMENTS = 5
MIN_COMPOSITION_THRESHOLD = 0.05  # 5% atomic fraction to be considered a principal element
BULK_MODULUS_COLUMN = "Bulk_Modulus"  # Adjust if column name differs in raw data
COMPOSITION_PREFIX = "element_"  # Prefix for element composition columns (e.g., element_Fe, element_Cr)

logger = get_logger(__name__)


def count_principal_elements(row: pd.Series, composition_cols: List[str], threshold: float = MIN_COMPOSITION_THRESHOLD) -> int:
    """
    Count the number of elements in a sample with atomic fraction >= threshold.

    Args:
        row: A pandas Series representing a single sample.
        composition_cols: List of column names containing element compositions.
        threshold: Minimum atomic fraction to count as a principal element.

    Returns:
        Integer count of principal elements.
    """
    if not composition_cols:
        return 0
    
    # Extract composition values for this row, handling potential NaNs
    compositions = row[composition_cols].fillna(0.0)
    
    # Count elements >= threshold
    count = (compositions >= threshold).sum()
    return int(count)


def filter_hea_samples(
    df: pd.DataFrame,
    min_elements: int = MIN_PRINCIPAL_ELEMENTS,
    composition_threshold: float = MIN_COMPOSITION_THRESHOLD,
    bulk_modulus_col: str = BULK_MODULUS_COLUMN,
    composition_prefix: str = COMPOSITION_PREFIX
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter a DataFrame of HEA samples to retain only valid entries.

    Criteria:
    1. At least `min_elements` principal elements (composition >= `composition_threshold`)
    2. Valid Bulk Modulus (not null, > 0)

    Args:
        df: Input DataFrame with composition and property columns.
        min_elements: Minimum number of principal elements required.
        composition_threshold: Atomic fraction threshold for principal elements.
        bulk_modulus_col: Name of the column containing Bulk Modulus values.
        composition_prefix: Prefix for element composition columns.

    Returns:
        Tuple of (filtered_df, stats_dict)
        stats_dict contains counts of dropped rows and reasons.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df, {"total_input": 0, "total_output": 0, "dropped_by_elements": 0, "dropped_by_bulk_modulus": 0}

    logger.info(f"Starting filter: min_elements={min_elements}, threshold={composition_threshold}")

    # Identify composition columns dynamically
    all_cols = df.columns.tolist()
    composition_cols = [c for c in all_cols if c.startswith(composition_prefix)]
    
    if not composition_cols:
        # Fallback: try to find columns that look like element compositions if prefix doesn't match
        # This might be needed if the data source uses different naming conventions
        logger.warning(f"No columns found with prefix '{composition_prefix}'. Attempting to detect composition columns...")
        # Simple heuristic: columns that are not standard metadata and have numeric values between 0 and 1
        # This is a fallback and might need adjustment based on actual data
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        potential_comp_cols = [c for c in numeric_cols if c.lower() not in ['bulk_modulus', 'formation_energy', 'density']]
        if potential_comp_cols:
            composition_cols = potential_comp_cols
            logger.info(f"Detected potential composition columns: {composition_cols[:5]}...")
        else:
            logger.error("Could not identify any composition columns. Cannot filter by element count.")
            raise ValueError("No composition columns found in the DataFrame.")

    logger.info(f"Identified {len(composition_cols)} composition columns.")

    # Create a copy to avoid SettingWithCopyWarning
    filtered_df = df.copy()

    # Step 1: Filter by Bulk Modulus validity
    initial_count = len(filtered_df)
    
    # Check if bulk modulus column exists
    if bulk_modulus_col not in filtered_df.columns:
        logger.warning(f"Bulk Modulus column '{bulk_modulus_col}' not found. Skipping bulk modulus filter.")
        bulk_modulus_valid_mask = pd.Series([True] * len(filtered_df), index=filtered_df.index)
    else:
        # Filter for non-null and positive Bulk Modulus
        bulk_modulus_valid_mask = filtered_df[bulk_modulus_col].notna() & (filtered_df[bulk_modulus_col] > 0)
        filtered_df = filtered_df[bulk_modulus_valid_mask]
    
    dropped_by_bulk_modulus = initial_count - len(filtered_df)
    logger.info(f"Dropped {dropped_by_bulk_modulus} samples due to invalid Bulk Modulus.")

    # Step 2: Filter by number of principal elements
    # Calculate count of principal elements for each row
    element_counts = filtered_df.apply(
        lambda row: count_principal_elements(row, composition_cols, composition_threshold),
        axis=1
    )
    
    valid_elements_mask = element_counts >= min_elements
    filtered_df = filtered_df[valid_elements_mask]
    
    dropped_by_elements = initial_count - dropped_by_bulk_modulus - len(filtered_df)
    logger.info(f"Dropped {dropped_by_elements} samples due to < {min_elements} principal elements.")

    final_count = len(filtered_df)
    logger.info(f"Filter complete. Input: {initial_count}, Output: {final_count} samples.")

    stats = {
        "total_input": initial_count,
        "total_output": final_count,
        "dropped_by_bulk_modulus": dropped_by_bulk_modulus,
        "dropped_by_elements": dropped_by_elements,
        "composition_columns_used": composition_cols,
        "min_elements_threshold": min_elements,
        "composition_threshold": composition_threshold
    }

    return filtered_df, stats


def main():
    """
    Main entry point for running the filter script.
    Expects input data in 'data/raw/hea_raw.csv' and outputs to 'data/processed/hea_filtered.csv'.
    """
    import os
    import sys
    from pathlib import Path

    # Setup logging
    init_logger = get_logger(__name__)
    init_logger.setLevel(logging.INFO)
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "raw" / "hea_raw.csv"
    output_path = project_root / "data" / "processed" / "hea_filtered.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure raw data has been fetched and placed at the expected location.")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows.")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    logger.info("Applying filters...")
    filtered_df, stats = filter_hea_samples(df)
    
    if filtered_df.empty:
        logger.warning("No samples passed the filters. Check your data and thresholds.")
    
    logger.info(f"Saving filtered data to {output_path}...")
    try:
        filtered_df.to_csv(output_path, index=False)
        logger.info("Saved successfully.")
        
        # Save stats to a JSON file for downstream tasks
        stats_path = project_root / "data" / "processed" / "filter_stats.json"
        import json
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Saved filter statistics to {stats_path}")
        
    except Exception as e:
        logger.error(f"Failed to save filtered data: {e}")
        sys.exit(1)

    logger.info("Filtering process completed.")


if __name__ == "__main__":
    main()
