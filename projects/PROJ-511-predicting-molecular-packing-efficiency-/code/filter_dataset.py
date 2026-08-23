"""
T016: Filter dataset records based on data quality criteria.

Reads: data/dataset_with_metrics.csv
Writes: data/dataset_filtered.csv

Filters out records where:
1. SMILES is missing or invalid (empty string, NaN, or None)
2. CAPE (Composition-Adjusted Packing Efficiency) is invalid (NaN, inf, or <= 0)
3. Raw Packing Coefficient (PC) is invalid (NaN, inf, or not in [0, 1])

This task ensures only high-quality, complete records proceed to downstream
analysis and modeling.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

from utils import setup_logging
from config import ensure_directories

logger = logging.getLogger(__name__)

# Constants
INPUT_FILE = os.path.join("data", "dataset_with_metrics.csv")
OUTPUT_FILE = os.path.join("data", "dataset_filtered.csv")

def validate_smiles(smiles: str) -> bool:
    """
    Check if SMILES string is valid and non-empty.

    Args:
        smiles: SMILES string to validate

    Returns:
        True if valid, False otherwise
    """
    if pd.isna(smiles) or smiles is None:
        return False
    smiles_str = str(smiles).strip()
    if not smiles_str or smiles_str.lower() in ['nan', 'none', '']:
        return False
    return True

def validate_numeric_metric(value: float, metric_name: str) -> bool:
    """
    Check if a numeric metric is valid (not NaN, not inf, positive).

    Args:
        value: Numeric value to validate
        metric_name: Name of the metric for logging

    Returns:
        True if valid, False otherwise
    """
    if pd.isna(value):
        logger.debug(f"Invalid {metric_name}: NaN")
        return False
    if not np.isfinite(value):
        logger.debug(f"Invalid {metric_name}: not finite")
        return False
    if value <= 0:
        logger.debug(f"Invalid {metric_name}: value <= 0 ({value})")
        return False
    return True

def validate_raw_pc(value: float) -> bool:
    """
    Check if Raw Packing Coefficient is valid (not NaN, not inf, and in [0, 1]).

    Args:
        value: Numeric value to validate

    Returns:
        True if valid, False otherwise
    """
    if pd.isna(value):
        logger.debug(f"Invalid Raw PC: NaN")
        return False
    if not np.isfinite(value):
        logger.debug(f"Invalid Raw PC: not finite")
        return False
    if value < 0 or value > 1:
        logger.debug(f"Invalid Raw PC: out of range [0, 1] ({value})")
        return False
    return True

def filter_dataset(input_path: str, output_path: str) -> Tuple[int, int, dict]:
    """
    Filter dataset based on SMILES and metric validity.

    Args:
        input_path: Path to input CSV
        output_path: Path to output filtered CSV

    Returns:
        Tuple of (original_count, filtered_count, filter_reasons)
    """
    logger.info(f"Loading dataset from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    original_count = len(df)
    logger.info(f"Loaded {original_count} records")

    # Track filtering reasons
    filter_reasons = {
        'missing_smiles': 0,
        'invalid_cape': 0,
        'invalid_raw_pc': 0,
        'multiple_issues': 0
    }

    # Identify rows to keep
    keep_mask = pd.Series([True] * len(df), index=df.index)
    reasons_mask = pd.Series([[] for _ in range(len(df))], index=df.index)

    # Check SMILES validity
    smiles_valid = df['smiles'].apply(validate_smiles)
    missing_smiles_mask = ~smiles_valid
    
    # Check CAPE validity
    cape_valid = df['cape'].apply(lambda x: validate_numeric_metric(x, 'CAPE'))
    invalid_cape_mask = ~cape_valid
    
    # Check Raw PC validity (must be in [0, 1])
    raw_pc_valid = df['raw_pc'].apply(validate_raw_pc)
    invalid_raw_pc_mask = ~raw_pc_valid

    # Combine masks and track reasons
    for idx in df.index:
        reasons = []
        if missing_smiles_mask.loc[idx]:
            reasons.append('missing_smiles')
        if invalid_cape_mask.loc[idx]:
            reasons.append('invalid_cape')
        if invalid_raw_pc_mask.loc[idx]:
            reasons.append('invalid_raw_pc')
        
        if len(reasons) > 0:
            keep_mask.loc[idx] = False
            reasons_mask.loc[idx] = reasons

    # Count reasons
    for idx in df.index:
        reasons = reasons_mask.loc[idx]
        if len(reasons) == 1:
            filter_reasons[reasons[0]] += 1
        elif len(reasons) > 1:
            filter_reasons['multiple_issues'] += 1

    # Apply filter
    filtered_df = df[keep_mask].reset_index(drop=True)
    filtered_count = len(filtered_df)
    removed_count = original_count - filtered_count

    logger.info(f"Filtering complete:")
    logger.info(f"  Original records: {original_count}")
    logger.info(f"  Removed records: {removed_count}")
    logger.info(f"  Remaining records: {filtered_count}")
    logger.info(f"  Filter reasons:")
    for reason, count in filter_reasons.items():
        if count > 0:
            logger.info(f"    {reason}: {count}")

    # Ensure output directory exists
    ensure_directories()

    # Write output
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered dataset written to {output_path}")

    return original_count, filtered_count, filter_reasons

def main():
    """Main entry point for filtering dataset."""
    # Setup logging
    setup_logging(level=logging.INFO)
    
    logger.info("Starting dataset filtering (T016)")
    
    try:
        original_count, filtered_count, filter_reasons = filter_dataset(
            INPUT_FILE, OUTPUT_FILE
        )
        
        if filtered_count == 0:
            logger.error("No records remaining after filtering!")
            return 1
        
        if filtered_count < 500:
            logger.error(f"Filtered dataset has only {filtered_count} records, which is less than the required 500!")
            return 1
        
        logger.info(f"Successfully filtered dataset: {original_count} -> {filtered_count} records")
        return 0
        
    except Exception as e:
        logger.error(f"Error during filtering: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())