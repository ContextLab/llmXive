"""
Runner script to fetch the ASSISTments dataset.

This script executes the fetch_assistments_dataset function and writes
the resulting data to disk. It is the entry point for T012.

Usage:
    python code/download/run_fetcher.py
"""

import os
import sys
import logging
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from download.fetch_assistments import fetch_assistments_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting ASSISTments dataset fetch (Task T012)...")
    
    # Fetch dataset with fallback
    df = fetch_assistments_dataset(
        use_cache=True,
        force_synthetic=False,
        min_rows=50
    )
    
    if df is None:
        logger.error("Failed to fetch or generate dataset.")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine which file was written
    if os.path.exists("data/raw/assistments_sample.csv"):
        output_file = "data/raw/assistments_sample.csv"
        source = "Real/Cached"
    else:
        output_file = "data/raw/assistments_synthetic_fallback.csv"
        source = "Synthetic"
        
    logger.info(f"Dataset loaded: {len(df)} rows from {source}.")
    logger.info(f"Schema: {list(df.columns)}")
    logger.info(f"Sample data:\n{df.head()}")
    
    # The fetch function already saves to disk, but we verify the file exists
    if os.path.exists(output_file):
        logger.info(f"Verification: Output file {output_file} exists.")
        logger.info("Task T012 completed successfully.")
    else:
        logger.error(f"Verification failed: Output file {output_file} not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
