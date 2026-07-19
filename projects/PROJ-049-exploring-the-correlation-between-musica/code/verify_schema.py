"""
Schema Verification Module.

Verifies the integrity and schema of output files.
"""

import os
import logging
import hashlib
import pandas as pd
from pathlib import Path
from utils import setup_logging

logger = setup_logging(__name__)
PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results")

def calculate_file_checksum(filepath: Path) -> str:
    """Calculate MD5 checksum of a file."""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def verify_schema_integrity():
    """
    Verify that output files exist and have expected columns.
    """
    logger.info("Verifying schema integrity...")
    
    files_to_check = [
        (PROCESSED_DIR / "merged_data.csv", ["user_id", "standard_genre", "listening_minutes"]),
        (PROCESSED_DIR / "analysis_results.csv", ["trait", "genre", "rho", "p_value"]),
        (RESULTS_DIR / "correlation_heatmap.png", None),
        (RESULTS_DIR / "results_report.csv", ["trait", "genre", "status"])
    ]
    
    all_ok = True
    for filepath, expected_cols in files_to_check:
        if not filepath.exists():
            logger.error(f"Missing file: {filepath}")
            all_ok = False
            continue
        
        if expected_cols:
            try:
                df = pd.read_csv(filepath)
                missing = [c for c in expected_cols if c not in df.columns]
                if missing:
                    logger.error(f"Missing columns in {filepath}: {missing}")
                    all_ok = False
                else:
                    checksum = calculate_file_checksum(filepath)
                    logger.info(f"Verified {filepath.name} (Checksum: {checksum})")
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
                all_ok = False
        else:
            logger.info(f"Verified file existence: {filepath.name}")
    
    if all_ok:
        logger.info("Schema verification successful.")
    else:
        logger.warning("Schema verification failed.")
        
    return all_ok

def main():
    """Entry point."""
    verify_schema_integrity()

if __name__ == "__main__":
    main()