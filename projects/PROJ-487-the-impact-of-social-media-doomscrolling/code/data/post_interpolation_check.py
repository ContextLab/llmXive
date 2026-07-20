import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any

# Add project root to path if running from script location
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from utils.logging import get_logger

# Constants
DATA_FILE = os.path.join(project_root, "data", "processed", "aligned_timeseries.csv")
OUTPUT_FILE = os.path.join(project_root, "data", "processed", "validation_status.json")
COMPLETENESS_THRESHOLD = 0.95  # 95%

logger = get_logger(__name__)

def calculate_completeness(df: pd.DataFrame) -> float:
    """
    Calculate the percentage of non-null values in the dataframe.
    Excludes the 'date' column from the calculation if present.
    """
    if df.empty:
        return 0.0

    # Identify numeric columns or specific data columns to check
    # Assuming the dataframe has a 'date' column and numeric time-series columns
    data_cols = [col for col in df.columns if col != 'date']

    if not data_cols:
        logger.warning("No data columns found to check for completeness.")
        return 0.0

    total_cells = df[data_cols].size
    non_null_cells = df[data_cols].count().sum()

    if total_cells == 0:
        return 0.0

    return non_null_cells / total_cells

def check_post_interpolation_completeness() -> Dict[str, Any]:
    """
    Main function to verify data completeness after interpolation.
    Reads aligned_timeseries.csv, calculates completeness, and writes validation_status.json.
    Exits with code 1 if completeness < 95%.
    """
    logger.info(f"Starting post-interpolation completeness check for {DATA_FILE}")

    # Check if file exists
    if not os.path.exists(DATA_FILE):
        error_msg = f"Error: Data file not found: {DATA_FILE}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "reason": "Data file not found",
            "file": DATA_FILE,
            "timestamp": datetime.now().isoformat()
        }

    try:
        df = pd.read_csv(DATA_FILE)
        logger.info(f"Loaded data: {len(df)} rows, {len(df.columns)} columns")

        completeness = calculate_completeness(df)
        logger.info(f"Calculated completeness: {completeness:.4f} ({completeness*100:.2f}%)")

        status = "passed" if completeness >= COMPLETENESS_THRESHOLD else "failed"
        result = {
            "status": status,
            "completeness": completeness,
            "threshold": COMPLETENESS_THRESHOLD,
            "file": DATA_FILE,
            "rows_checked": len(df),
            "timestamp": datetime.now().isoformat()
        }

        if status == "failed":
            error_msg = f"Data completeness {completeness*100:.2f}% is below threshold {COMPLETENESS_THRESHOLD*100:.2f}%"
            logger.error(error_msg)
            # Do not exit here, return status to let caller decide, 
            # but per spec we must exit non-zero if failed.
            # We will handle the exit in main() after saving the status.

        # Save validation status
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Validation status written to {OUTPUT_FILE}")

        return result

    except Exception as e:
        error_msg = f"Error during completeness check: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "failed",
            "reason": str(e),
            "file": DATA_FILE,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Entry point for the script."""
    result = check_post_interpolation_completeness()
    
    if result["status"] == "failed":
        logger.error("Post-interpolation completeness check FAILED.")
        sys.exit(1)
    
    logger.info("Post-interpolation completeness check PASSED.")
    sys.exit(0)

if __name__ == "__main__":
    main()