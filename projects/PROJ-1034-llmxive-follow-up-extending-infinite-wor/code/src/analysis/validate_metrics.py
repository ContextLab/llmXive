"""
Validation script for simulation metrics.

Tasks:
1. Scan Parquet files for NaN values (T017 requirement).
2. Validate Time-Bound Baseline runs (T057 requirement):
   - Check for 'Time-Bound' flag in metadata/status.
   - Verify step count >= 1000.
   - Fail if the partial run is too short to be statistically meaningful.
"""
import os
import sys
import glob
import logging
import pandas as pd
import json
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/validate_metrics.log')
    ]
)
logger = logging.getLogger(__name__)

def scan_parquet_for_nans(file_path: str) -> Tuple[bool, int]:
    """
    Scan a Parquet file for NaN values.
    
    Returns:
        Tuple of (has_nans, count_of_nans)
    """
    try:
        df = pd.read_parquet(file_path)
        nan_count = df.isna().sum().sum()
        has_nans = nan_count > 0
        if has_nans:
            logger.warning(f"Found {nan_count} NaN values in {file_path}")
        else:
            logger.info(f"No NaN values found in {file_path}")
        return has_nans, int(nan_count)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        raise

def validate_time_bound_baseline(file_path: str) -> Tuple[bool, str]:
    """
    Validate a Time-Bound Baseline run (T057 requirement).
    
    Checks:
    1. Presence of 'Time-Bound' flag in metadata or status.
    2. Step count >= 1000.
    
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        df = pd.read_parquet(file_path)
        
        # Check step count
        # Assuming the dataframe has a 'step' column or we count rows
        if 'step' in df.columns:
            max_step = df['step'].max()
            step_count = len(df)
        else:
            # Fallback: count rows if no step column
            step_count = len(df)
            max_step = step_count - 1
        
        if step_count < 1000:
            return False, f"Step count ({step_count}) is less than minimum required 1000."
        
        # Check for 'Time-Bound' flag
        # Look for it in metadata, or a specific column if it exists
        has_flag = False
        
        # Check dataframe columns for a flag
        flag_cols = ['is_time_bound', 'time_bound', 'flag', 'status']
        for col in flag_cols:
            if col in df.columns:
                if df[col].any():
                    has_flag = True
                    break
        
        # If not in columns, check metadata (if available in pandas parquet metadata)
        if not has_flag and hasattr(df, 'attrs'):
            if df.attrs.get('time_bound', False) or df.attrs.get('is_time_bound', False):
                has_flag = True
        
        # If still not found, try reading the associated status JSON if it exists
        # Expected pattern: data/raw/baseline_partial.parquet -> data/raw/baseline_partial_status.json
        status_path = file_path.replace('.parquet', '_status.json')
        if not has_flag and os.path.exists(status_path):
            try:
                with open(status_path, 'r') as f:
                    status_data = json.load(f)
                if status_data.get('time_bound', False) or status_data.get('is_time_bound', False):
                    has_flag = True
            except Exception:
                pass
        
        if not has_flag:
            return False, "Missing 'Time-Bound' flag in metadata or data."
        
        return True, f"Validation passed: {step_count} steps, Time-Bound flag present."
        
    except Exception as e:
        logger.error(f"Error validating time-bound baseline {file_path}: {e}")
        raise

def validate_metrics_directory(directory: str) -> bool:
    """
    Validate all Parquet files in a directory.
    
    - Scans for NaNs (T017).
    - Specifically validates baseline_partial.parquet for T057 requirements.
    
    Returns:
        True if all validations pass, False otherwise.
    """
    all_valid = True
    parquet_files = glob.glob(os.path.join(directory, "*.parquet"))
    
    if not parquet_files:
        logger.warning(f"No Parquet files found in {directory}")
        return False
    
    for file_path in parquet_files:
        logger.info(f"Validating {file_path}")
        
        # T017: Check for NaNs
        has_nans, nan_count = scan_parquet_for_nans(file_path)
        if has_nans:
            all_valid = False
        
        # T057: Special validation for baseline_partial.parquet
        if 'baseline_partial.parquet' in os.path.basename(file_path):
            logger.info("Performing Time-Bound Baseline validation (T057)...")
            is_valid, message = validate_time_bound_baseline(file_path)
            if is_valid:
                logger.info(f"Time-Bound Baseline validation PASSED: {message}")
            else:
                logger.error(f"Time-Bound Baseline validation FAILED: {message}")
                all_valid = False
        
    return all_valid

def main():
    """Main entry point for the validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate simulation metrics.")
    parser.add_argument("--path", type=str, default="data/raw",
                        help="Path to directory containing Parquet files")
    args = parser.parse_args()
    
    if not os.path.isdir(args.path):
        logger.error(f"Directory not found: {args.path}")
        sys.exit(1)
    
    logger.info(f"Starting validation on {args.path}")
    success = validate_metrics_directory(args.path)
    
    if success:
        logger.info("All validations passed.")
        sys.exit(0)
    else:
        logger.error("Validation failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()