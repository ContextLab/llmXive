"""
Validation metrics module for the llmXive simulation pipeline.

This module provides functions to validate simulation outputs,
specifically checking for NaN values, time-bound flags, and
minimum step counts in partial runs.
"""
import os
import sys
import glob
import logging
import pandas as pd
import json
from pathlib import Path
from typing import Optional, Tuple, List

# Configure logging
logger = logging.getLogger(__name__)

def scan_parquet_for_nans(file_path: str) -> Tuple[bool, int]:
    """
    Scan a Parquet file for NaN values.
    
    Args:
        file_path: Path to the Parquet file.
        
    Returns:
        Tuple of (has_nans, count_of_nans)
    """
    try:
        df = pd.read_parquet(file_path)
        nan_count = df.isna().sum().sum()
        has_nans = nan_count > 0
        return has_nans, int(nan_count)
    except Exception as e:
        logger.error(f"Error scanning {file_path} for NaNs: {e}")
        raise

def validate_time_bound_baseline(file_path: str, min_steps: int = 1000) -> Tuple[bool, bool, str]:
    """
    Validate a time-bound baseline run.
    
    This function checks:
    1. Presence of the 'Time-Bound' flag in the metadata/status.
    2. That the partial run contains at least min_steps rows.
    
    Args:
        file_path: Path to the baseline_partial.parquet file.
        min_steps: Minimum required number of steps.
        
    Returns:
        Tuple of (has_time_bound_flag, meets_min_steps, status_message)
    """
    if not os.path.exists(file_path):
        return False, False, f"File not found: {file_path}"
    
    try:
        df = pd.read_parquet(file_path)
        total_steps = len(df)
        
        # Check for Time-Bound flag
        # The flag might be in a 'status' column or metadata
        has_time_bound = False
        
        # Check columns for status flag
        if 'status' in df.columns:
            # Check if any row indicates Time-Bound
            time_bound_values = df['status'].astype(str).str.contains('Time-Bound', case=False, na=False)
            has_time_bound = time_bound_values.any()
        
        # If not in status column, check metadata or a dedicated flag column
        if not has_time_bound:
            if 'time_bound' in df.columns:
                has_time_bound = df['time_bound'].any()
            elif 'flags' in df.columns:
                # Assume flags might be a list or string containing 'Time-Bound'
                flags_str = str(df['flags'].iloc[0]) if len(df) > 0 else ""
                has_time_bound = 'Time-Bound' in flags_str
        
        # Check minimum steps
        meets_min = total_steps >= min_steps
        
        if not has_time_bound:
            msg = f"Missing 'Time-Bound' flag. Steps: {total_steps}"
            return False, meets_min, msg
        
        if not meets_min:
            msg = f"Time-Bound flag present, but steps ({total_steps}) < min_steps ({min_steps})"
            return True, False, msg
        
        return True, True, f"Validation passed: {total_steps} steps with Time-Bound flag"
        
    except Exception as e:
        logger.error(f"Error validating {file_path}: {e}")
        return False, False, f"Validation error: {e}"

def validate_metrics_directory(directory: str, min_steps: int = 1000) -> bool:
    """
    Validate all parquet files in a directory.
    
    Args:
        directory: Path to the directory containing parquet files.
        min_steps: Minimum steps required for time-bound baselines.
        
    Returns:
        True if all validations pass, False otherwise.
    """
    all_valid = True
    
    # Check for baseline_partial.parquet specifically
    baseline_path = os.path.join(directory, "baseline_partial.parquet")
    if os.path.exists(baseline_path):
        logger.info(f"Validating baseline_partial.parquet...")
        has_flag, meets_steps, msg = validate_time_bound_baseline(baseline_path, min_steps)
        logger.info(f"  Result: {msg}")
        if not has_flag or not meets_steps:
            all_valid = False
    else:
        logger.warning(f"baseline_partial.parquet not found in {directory}")
        all_valid = False
    
    # Check other parquet files for NaNs
    parquet_files = glob.glob(os.path.join(directory, "*.parquet"))
    for pf in parquet_files:
        if "baseline_partial.parquet" in pf:
            continue
        
        logger.info(f"Checking {pf} for NaNs...")
        has_nans, count = scan_parquet_for_nans(pf)
        if has_nans:
            logger.error(f"  Found {count} NaN values in {pf}")
            all_valid = False
        else:
            logger.info(f"  No NaN values found.")
    
    return all_valid

def main():
    """Main entry point for validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate simulation metrics")
    parser.add_argument("--path", type=str, default="data/raw",
                      help="Directory containing parquet files to validate")
    parser.add_argument("--min-steps", type=int, default=1000,
                      help="Minimum steps required for time-bound baseline")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    success = validate_metrics_directory(args.path, args.min_steps)
    
    if success:
        logger.info("All validations passed.")
        sys.exit(0)
    else:
        logger.error("Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
