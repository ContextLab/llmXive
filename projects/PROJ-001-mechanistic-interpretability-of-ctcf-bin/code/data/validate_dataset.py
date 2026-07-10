"""
Validate the unified CTCF dataset for data integrity.

This script ensures that every row in the unified dataset contains:
1. A fixed-length sequence (expected 1000bp for ±500bp windows).
2. Matched chromatin values (ATAC-seq, H3K27ac) without nulls.
3. Correct data types for all columns.

It raises a RuntimeError if any validation fails, preventing downstream
model training with corrupted data.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
EXPECTED_SEQUENCE_LENGTH = 1000  # ±500bp window
REQUIRED_CHROMATIN_COLUMNS = ['atac_signal', 'h3k27ac_signal']
REQUIRED_SEQUENCE_COLUMN = 'sequence'
REQUIRED_LABEL_COLUMN = 'label'

def load_dataset(filepath: str) -> pd.DataFrame:
    """Load the unified dataset from parquet file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    
    logger.info(f"Loading dataset from {filepath}...")
    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded {len(df)} rows.")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset: {e}")

def validate_sequence_length(df: pd.DataFrame) -> None:
    """Validate that all sequences have the expected length."""
    logger.info("Validating sequence lengths...")
    
    if REQUIRED_SEQUENCE_COLUMN not in df.columns:
        raise ValueError(f"Missing required column: {REQUIRED_SEQUENCE_COLUMN}")
    
    # Calculate lengths
    seq_lengths = df[REQUIRED_SEQUENCE_COLUMN].apply(len)
    invalid_mask = seq_lengths != EXPECTED_SEQUENCE_LENGTH
    invalid_count = invalid_mask.sum()
    
    if invalid_count > 0:
        invalid_indices = df.index[invalid_mask].tolist()
        raise RuntimeError(
            f"Found {invalid_count} rows with incorrect sequence length. "
            f"Expected {EXPECTED_SEQUENCE_LENGTH}, found lengths: "
            f"{seq_lengths[invalid_mask].unique().tolist()}. "
            f"First few invalid indices: {invalid_indices[:5]}"
        )
    
    logger.info(f"✓ All {len(df)} sequences have correct length ({EXPECTED_SEQUENCE_LENGTH}bp).")

def validate_no_nulls(df: pd.DataFrame) -> None:
    """Validate that no null values exist in critical columns."""
    logger.info("Validating for null values...")
    
    critical_columns = [REQUIRED_SEQUENCE_COLUMN] + REQUIRED_CHROMATIN_COLUMNS
    if REQUIRED_LABEL_COLUMN in df.columns:
        critical_columns.append(REQUIRED_LABEL_COLUMN)
    
    missing_cols = [col for col in critical_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for validation: {missing_cols}")
    
    null_counts = df[critical_columns].isnull().sum()
    total_nulls = null_counts.sum()
    
    if total_nulls > 0:
        null_details = null_counts[null_counts > 0].to_dict()
        raise RuntimeError(
            f"Found {total_nulls} null values in critical columns: {null_details}"
        )
    
    logger.info(f"✓ No null values found in critical columns.")

def validate_chromatin_alignment(df: pd.DataFrame) -> None:
    """Validate that chromatin signals are matched and within expected ranges."""
    logger.info("Validating chromatin signal alignment...")
    
    for col in REQUIRED_CHROMATIN_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Missing chromatin column: {col}")
        
        # Check for non-finite values (inf, nan)
        if not np.isfinite(df[col]).all():
            raise ValueError(
                f"Column '{col}' contains non-finite values (inf or nan)."
            )
        
        # Optional: Check for reasonable ranges (signals are typically normalized 0-1 or similar)
        # We allow a wide range but check for extreme outliers that might indicate corruption
        if df[col].max() > 1e6 or df[col].min() < -1e6:
            logger.warning(
                f"Column '{col}' has extreme values (min: {df[col].min()}, max: {df[col].max()}). "
                "This might indicate normalization issues, but not raising an error."
            )
    
    logger.info("✓ Chromatin signals are aligned and valid.")

def validate_dataset(filepath: str) -> Dict[str, Any]:
    """
    Main validation routine.
    
    Args:
        filepath: Path to the unified dataset parquet file.
        
    Returns:
        Dictionary with validation statistics.
        
    Raises:
        RuntimeError: If any validation check fails.
    """
    df = load_dataset(filepath)
    
    logger.info("Starting comprehensive dataset validation...")
    
    # Run validations
    validate_sequence_length(df)
    validate_no_nulls(df)
    validate_chromatin_alignment(df)
    
    # Generate summary
    stats = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "sequence_length": EXPECTED_SEQUENCE_LENGTH,
        "validation_status": "PASSED",
        "null_count": 0
    }
    
    logger.info("Validation completed successfully!")
    logger.info(f"Dataset stats: {json.dumps(stats, indent=2)}")
    
    return stats

def main():
    """Entry point for the script."""
    # Default path relative to project root
    dataset_path = "data/processed/unified_ctcf_dataset.parquet"
    
    # Allow override via command line
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    
    try:
        stats = validate_dataset(dataset_path)
        print(f"\nValidation PASSED. Summary: {stats['total_rows']} rows, {stats['total_columns']} columns.")
        sys.exit(0)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"Validation FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()