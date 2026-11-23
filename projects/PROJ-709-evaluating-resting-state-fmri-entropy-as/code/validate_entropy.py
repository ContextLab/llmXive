"""
Validation module for entropy feature outputs.

This module implements T019: Add validation to ensure no NaN values in the final
CSV and verify that entropy values lie within a biologically plausible range.

Biological Plausibility Range for Sample Entropy (SampEn):
- SampEn is typically non-negative.
- For fMRI time series with m=2, r=0.2*SD, values usually fall between 0.0 and 2.5.
- Values > 3.0 are extremely rare and likely indicate noise or artifacts.
- Values < 0.0 are mathematically impossible for SampEn.

Success Criteria:
- No NaN values in the feature matrix.
- All values >= 0.0.
- All values <= 3.0 (configurable upper bound).
- Report generation with summary statistics.
"""
import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Import config for hyperparameters
import config

# Setup logger
def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Setup a logger with console and optional file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

logger = setup_logger(__name__)

# Biologically plausible range constants
DEFAULT_MIN_ENTROPY = 0.0
DEFAULT_MAX_ENTROPY = 3.0

def validate_entropy_csv(
    csv_path: str,
    min_val: float = DEFAULT_MIN_ENTROPY,
    max_val: float = DEFAULT_MAX_ENTROPY
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate the entropy features CSV file.
    
    Checks:
    1. File exists and is readable.
    2. No NaN values in the feature columns.
    3. All values are within the biologically plausible range [min_val, max_val].
    
    Args:
        csv_path: Path to the entropy features CSV file.
        min_val: Minimum acceptable entropy value (default: 0.0).
        max_val: Maximum acceptable entropy value (default: 3.0).
    
    Returns:
        Tuple of (is_valid, details_dict) where:
            - is_valid: True if all checks pass.
            - details_dict: Contains statistics and error messages if any.
    
    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV is empty or has no data rows.
    """
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    logger.info(f"Validating entropy CSV: {csv_path}")
    
    # Load the CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")
    
    if df.empty:
        raise ValueError("CSV file is empty")
    
    # Identify feature columns (exclude subject_id if present)
    # Assuming first column is subject_id or similar identifier
    feature_columns = [col for col in df.columns if col != 'subject_id']
    
    if not feature_columns:
        raise ValueError("No feature columns found in CSV")
    
    logger.info(f"Found {len(feature_columns)} feature columns")
    logger.info(f"Dataset shape: {df.shape}")
    
    # Check 1: No NaN values
    nan_counts = df[feature_columns].isna().sum()
    total_nans = nan_counts.sum()
    
    details = {
        "file_path": str(csv_path),
        "shape": list(df.shape),
        "n_subjects": len(df),
        "n_features": len(feature_columns),
        "total_nans": int(total_nans),
        "nan_per_feature": nan_counts.to_dict(),
        "min_entropy": float(df[feature_columns].min().min()),
        "max_entropy": float(df[feature_columns].max().max()),
        "mean_entropy": float(df[feature_columns].mean().mean()),
        "std_entropy": float(df[feature_columns].std().mean()),
        "is_valid": True,
        "errors": []
    }
    
    if total_nans > 0:
        msg = f"Found {total_nans} NaN values in the feature matrix"
        logger.error(msg)
        details["errors"].append(msg)
        details["is_valid"] = False
    else:
        logger.info("✓ No NaN values found")
    
    # Check 2: Values within biologically plausible range
    out_of_range_low = (df[feature_columns] < min_val).sum().sum()
    out_of_range_high = (df[feature_columns] > max_val).sum().sum()
    
    if out_of_range_low > 0:
        msg = f"Found {out_of_range_low} values below minimum threshold ({min_val})"
        logger.warning(msg)
        details["errors"].append(msg)
        details["is_valid"] = False
        details["n_below_min"] = int(out_of_range_low)
    else:
        logger.info(f"✓ All values >= {min_val}")
    
    if out_of_range_high > 0:
        msg = f"Found {out_of_range_high} values above maximum threshold ({max_val})"
        logger.warning(msg)
        details["errors"].append(msg)
        details["is_valid"] = False
        details["n_above_max"] = int(out_of_range_high)
    else:
        logger.info(f"✓ All values <= {max_val}")
    
    return details["is_valid"], details

def main():
    """
    Main entry point for entropy validation script.
    
    Usage:
        python code/validate_entropy.py --input data/processed/subject_entropy_features.csv
    """
    parser = argparse.ArgumentParser(
        description="Validate entropy features CSV for NaN values and biological plausibility."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to the entropy features CSV file to validate."
    )
    parser.add_argument(
        "--min",
        type=float,
        default=DEFAULT_MIN_ENTROPY,
        help=f"Minimum acceptable entropy value (default: {DEFAULT_MIN_ENTROPY})"
    )
    parser.add_argument(
        "--max",
        type=float,
        default=DEFAULT_MAX_ENTROPY,
        help=f"Maximum acceptable entropy value (default: {DEFAULT_MAX_ENTROPY})"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to write validation report JSON (optional)."
    )
    
    args = parser.parse_args()
    
    try:
        is_valid, details = validate_entropy_csv(
            args.input,
            min_val=args.min,
            max_val=args.max
        )
        
        # Print summary
        print("\n" + "="*60)
        print("ENTROPY VALIDATION REPORT")
        print("="*60)
        print(f"File: {details['file_path']}")
        print(f"Shape: {details['n_subjects']} subjects x {details['n_features']} features")
        print(f"Total NaNs: {details['total_nans']}")
        print(f"Min Entropy: {details['min_entropy']:.4f}")
        print(f"Max Entropy: {details['max_entropy']:.4f}")
        print(f"Mean Entropy: {details['mean_entropy']:.4f}")
        print(f"Std Entropy: {details['std_entropy']:.4f}")
        print("-"*60)
        
        if details["is_valid"]:
            print("RESULT: ✓ VALID - All checks passed.")
        else:
            print("RESULT: ✗ INVALID - One or more checks failed.")
            print("Errors:")
            for err in details["errors"]:
                print(f"  - {err}")
        
        print("="*60 + "\n")
        
        # Write JSON report if requested
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(details, f, indent=2)
            logger.info(f"Validation report written to: {args.output}")
        
        # Exit with appropriate code
        sys.exit(0 if details["is_valid"] else 1)
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
