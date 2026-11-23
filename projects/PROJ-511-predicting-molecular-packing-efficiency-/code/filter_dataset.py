"""
Task T016: Filter dataset records based on SMILES validity and metric ranges.

Reads: data/dataset_with_metrics.csv
Writes: data/dataset_filtered.csv

Logic:
1. Remove rows where 'smiles' is null or empty.
2. Remove rows where 'raw_pc' is not in [0, 1] or is NaN.
3. Remove rows where 'cape' is NaN or infinite.
4. Log counts of removed records and reasons.
5. Assert final row count >= 500, else exit with error.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional

# Configure logging to stdout for pipeline visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths relative to project root
INPUT_PATH = "data/dataset_with_metrics.csv"
OUTPUT_PATH = "data/dataset_filtered.csv"
MIN_ROWS = 500

def validate_smiles(smiles: Optional[str]) -> bool:
    """Check if SMILES string is valid (non-null, non-empty)."""
    if smiles is None:
        return False
    if not isinstance(smiles, str):
        return False
    return len(smiles.strip()) > 0

def validate_numeric_metric(value: float) -> bool:
    """Check if a numeric value is finite (not NaN, not Inf)."""
    if pd.isna(value):
        return False
    if np.isinf(value):
        return False
    return True

def validate_raw_pc(pc: float) -> bool:
    """Check if PC_raw is in the valid range [0, 1]."""
    if not validate_numeric_metric(pc):
        return False
    return 0.0 <= pc <= 1.0

def filter_dataset(input_path: str, output_path: str) -> Tuple[int, int, int, int]:
    """
    Filter the dataset based on validity rules.
    
    Returns:
        Tuple of (total_rows, valid_rows, removed_smiles, removed_pc, removed_cape)
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)
    total_rows = len(df)
    logger.info(f"Loaded {total_rows} rows.")
    
    # Track removal reasons
    initial_mask = pd.Series([True] * len(df), index=df.index)
    
    # 1. Filter invalid SMILES
    smiles_mask = df['smiles'].apply(validate_smiles)
    invalid_smiles_count = (~smiles_mask).sum()
    logger.info(f"Removing {invalid_smiles_count} rows with invalid/missing SMILES.")
    
    # 2. Filter invalid PC_raw (must be in [0, 1])
    pc_mask = df['raw_pc'].apply(validate_raw_pc)
    invalid_pc_count = (~pc_mask).sum()
    logger.info(f"Removing {invalid_pc_count} rows with invalid PC_raw (not in [0, 1] or NaN/Inf).")
    
    # 3. Filter invalid CAPE (must be finite)
    cape_mask = df['cape'].apply(validate_numeric_metric)
    invalid_cape_count = (~cape_mask).sum()
    logger.info(f"Removing {invalid_cape_count} rows with invalid CAPE (NaN or Inf).")
    
    # Combine masks: keep only rows where ALL conditions are met
    final_mask = smiles_mask & pc_mask & cape_mask
    filtered_df = df[final_mask].reset_index(drop=True)
    final_count = len(filtered_df)
    
    # Log summary
    removed_count = total_rows - final_count
    logger.info(f"Total rows removed: {removed_count}")
    logger.info(f"Final dataset size: {final_count} rows.")
    
    if final_count < MIN_ROWS:
        logger.error(f"Dataset size ({final_count}) is below the minimum threshold of {MIN_ROWS}.")
        logger.error("Failing task T016 as per specification requirements.")
        raise ValueError(f"Filtered dataset has {final_count} rows, which is less than the required minimum of {MIN_ROWS}.")
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered dataset saved to {output_path}")
    
    return total_rows, final_count, invalid_smiles_count, invalid_pc_count, invalid_cape_count

def main():
    """Main entry point for the filtering script."""
    try:
        logger.info("Starting T016: Filter Dataset")
        total, valid, bad_smiles, bad_pc, bad_cape = filter_dataset(INPUT_PATH, OUTPUT_PATH)
        logger.info("T016 completed successfully.")
        logger.info(f"Summary: Total={total}, Valid={valid}, BadSMILES={bad_smiles}, BadPC={bad_pc}, BadCAPE={bad_cape}")
    except Exception as e:
        logger.error(f"T016 failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()