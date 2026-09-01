import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
DATA_PROCESSED_DIR = project_root / "data" / "processed"
OUTPUT_FILE = DATA_PROCESSED_DIR / "aligned_timeseries.csv"
THRESHOLD = 0.95  # 95% completeness requirement


def calculate_completeness(df: pd.DataFrame) -> float:
    """
    Calculate the data completeness ratio.
    Completeness = (Count of non-null rows) / (Total rows in the DataFrame)
    
    This assumes the DataFrame has already been aligned to the intersection range.
    """
    if df.empty:
        return 0.0
    
    total_rows = len(df)
    non_null_rows = df.dropna().shape[0]
    
    completeness = non_null_rows / total_rows
    return completeness


def check_post_interpolation_completeness() -> bool:
    """
    Main validation logic for Task T023.
    
    1. Loads 'data/processed/aligned_timeseries.csv'.
    2. Calculates completeness (non-null rows / total rows).
    3. Compares against 95% threshold.
    4. Prints status and exits with code 1 if failed, 0 if passed.
    
    Returns:
        bool: True if check passes, False otherwise.
    """
    logger.info(f"Starting post-interpolation completeness check for {OUTPUT_FILE}")
    
    if not OUTPUT_FILE.exists():
        logger.error(f"Output file not found: {OUTPUT_FILE}")
        print(f"ERROR: Required file not found: {OUTPUT_FILE}")
        return False
    
    try:
        df = pd.read_csv(OUTPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to read {OUTPUT_FILE}: {e}")
        print(f"ERROR: Failed to read CSV: {e}")
        return False
    
    if df.empty:
        logger.error("Loaded DataFrame is empty.")
        print("ERROR: Loaded data is empty.")
        return False
    
    completeness = calculate_completeness(df)
    logger.info(f"Calculated completeness: {completeness:.4f} ({completeness*100:.2f}%)")
    
    is_valid = completeness >= THRESHOLD
    
    status_msg = "PASSED" if is_valid else "FAILED"
    print(f"Post-Interpolation Completeness Check: {status_msg}")
    print(f"  - File: {OUTPUT_FILE.name}")
    print(f"  - Total Rows: {len(df)}")
    print(f"  - Non-Null Rows: {df.dropna().shape[0]}")
    print(f"  - Completeness: {completeness*100:.2f}%")
    print(f"  - Threshold: {THRESHOLD*100:.2f}%")
    
    if not is_valid:
        logger.error(f"Completeness {completeness:.4f} is below threshold {THRESHOLD}")
        return False
    
    logger.info("Completeness check passed.")
    return True


def main():
    """Entry point for the script."""
    success = check_post_interpolation_completeness()
    if not success:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()