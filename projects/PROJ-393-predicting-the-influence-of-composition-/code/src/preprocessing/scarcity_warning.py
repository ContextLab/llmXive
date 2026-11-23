"""
Scarcity Warning Module for T028b.

Implements the logic to count rows in the preprocessed dataset and write
a flag file (data/.scarcity_warning) if the count is below the threshold (50).
"""
import logging
import json
import sys
from pathlib import Path
from typing import Optional
import pandas as pd

from src.utils.logging_config import setup_logging, create_logger

# Constants
SCARCITY_THRESHOLD = 50
INPUT_FILE = Path("data/processed/alloys_raw.csv")
OUTPUT_FILE = Path("data/.scarcity_warning")

logger = create_logger(__name__)


def load_processed_data() -> pd.DataFrame:
    """Load the preprocessed alloys dataset."""
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
    
    try:
        df = pd.read_csv(INPUT_FILE)
        logger.info(f"Loaded {len(df)} rows from {INPUT_FILE}")
        return df
    except Exception as e:
        logger.error(f"Failed to load {INPUT_FILE}: {e}")
        raise


def check_and_warn() -> dict:
    """
    Count rows in the preprocessed dataset and generate a scarcity warning.
    
    Returns:
        dict: Status report containing 'n' (count), 'threshold', and 'warning_generated'.
    """
    df = load_processed_data()
    n = len(df)
    
    logger.info(f"Row count check: N={n}, Threshold={SCARCITY_THRESHOLD}")
    
    warning_content = {}
    warning_generated = False
    
    if n < SCARCITY_THRESHOLD:
        warning_content = {
            "n": n,
            "threshold": SCARCITY_THRESHOLD
        }
        warning_generated = True
        logger.warning(f"DATA SCARCITY DETECTED: N={n} < {SCARCITY_THRESHOLD}. Generating warning flag.")
    else:
        logger.info(f"Data volume sufficient: N={n} >= {SCARCITY_THRESHOLD}. No warning generated.")
    
    # Write the output file
    try:
        # Ensure the data directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_FILE, 'w') as f:
            if warning_generated:
                json.dump(warning_content, f, indent=2)
            else:
                # Write an empty file if no warning is needed
                f.write("")
        
        logger.info(f"Scarcity check result written to {OUTPUT_FILE}")
        
    except Exception as e:
        logger.error(f"Failed to write scarcity warning file: {e}")
        raise
    
    return {
        "n": n,
        "threshold": SCARCITY_THRESHOLD,
        "warning_generated": warning_generated,
        "warning_content": warning_content if warning_generated else None
    }


def main():
    """Entry point for the script."""
    setup_logging()
    try:
        result = check_and_warn()
        logger.info(f"Task T028b completed successfully: {result}")
        return 0
    except Exception as e:
        logger.error(f"Task T028b failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())