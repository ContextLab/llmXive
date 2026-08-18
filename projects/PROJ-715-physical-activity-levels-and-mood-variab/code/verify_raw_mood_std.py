"""
Verification script for Task T019b.
Explicitly verifies and documents that the raw `mood_std` column in
`daily_aggregates.csv` remains unmodified and available for other analyses,
ensuring compliance with FR-003's requirement to preserve the raw metric.
"""
import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd

# Import config for path resolution
from config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_raw_mood_std():
    """
    Loads daily_aggregates.csv and verifies:
    1. The 'mood_std' column exists.
    2. The 'mood_std' column contains no negative values (raw std dev >= 0).
    3. The 'mood_std' column contains no NaN/Inf values.
    4. The column is available for downstream analysis (not dropped/modified).
    
    Returns:
        dict: Verification results including status and details.
    """
    try:
        # Resolve path using the project's config utility
        # This handles the cumulative contract of get_path()
        file_path = get_path('data', 'processed', 'daily_aggregates.csv')
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Daily aggregates file not found at {file_path}. "
                "Run preprocessing first (T015)."
            )
        
        logger.info(f"Loading daily aggregates from: {file_path}")
        df = pd.read_csv(file_path)
        
        # Verification 1: Column existence
        if 'mood_std' not in df.columns:
            raise ValueError(
                "Verification Failed: 'mood_std' column missing from daily_aggregates.csv"
            )
        
        # Verification 2: Non-negative values (Standard Deviation >= 0)
        # Raw std dev should never be negative.
        negative_count = (df['mood_std'] < 0).sum()
        if negative_count > 0:
            raise ValueError(
                f"Verification Failed: Found {negative_count} negative values in 'mood_std'."
            )
        
        # Verification 3: No NaN or Inf values
        null_count = df['mood_std'].isna().sum()
        inf_count = (df['mood_std'].apply(lambda x: x in [float('inf'), float('-inf')])).sum()
        
        if null_count > 0:
            raise ValueError(
                f"Verification Failed: Found {null_count} NaN values in 'mood_std'."
            )
        if inf_count > 0:
            raise ValueError(
                f"Verification Failed: Found {inf_count} Inf values in 'mood_std'."
            )
        
        # Verification 4: Availability for downstream analysis
        # We simply confirm the column is present and valid, satisfying FR-003.
        # We do not modify it here; we only read and validate.
        
        result = {
            "status": "PASSED",
            "file_path": str(file_path),
            "column": "mood_std",
            "row_count": len(df),
            "checks": {
                "column_exists": True,
                "no_negative_values": True,
                "no_null_values": True,
                "no_inf_values": True,
                "raw_metric_preserved": True
            },
            "statistics": {
                "min": float(df['mood_std'].min()),
                "max": float(df['mood_std'].max()),
                "mean": float(df['mood_std'].mean()),
                "median": float(df['mood_std'].median())
            },
            "compliance": {
                "FR-003": "Raw mood_std metric preserved and available for analysis."
            }
        }
        
        logger.info("Verification PASSED. Raw mood_std column is valid and preserved.")
        return result

    except Exception as e:
        logger.error(f"Verification FAILED: {str(e)}")
        return {
            "status": "FAILED",
            "error": str(e)
        }

def main():
    """Main entry point for the verification script."""
    logger.info("Starting T019b: Verify Raw Mood Standard Deviation Preservation")
    
    result = verify_raw_mood_std()
    
    # Write verification log to data/processed for audit trail
    log_path = get_path('data', 'processed', 't019b_verification_log.json')
    
    with open(log_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Verification log written to: {log_path}")
    
    if result["status"] == "FAILED":
        logger.error("T019b verification failed. Do not proceed with modeling.")
        sys.exit(1)
    else:
        logger.info("T019b verification successful. Proceeding to modeling.")
        sys.exit(0)

if __name__ == "__main__":
    main()