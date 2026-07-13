import os
import sys
import json
import logging
from typing import List, Dict, Any
from data_loader import download_dataset
from analysis import run_baseline_analysis
from config import Config
from utils import setup_logging

logger = logging.getLogger(__name__)

def main():
    setup_logging("INFO")
    config = Config()
    
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_path = config.get("OUTPUT_PATH", "data/processed/baseline_metrics.json")
    
    # Ensure raw directory exists
    os.makedirs(raw_dir, exist_ok=True)
    
    # If no data exists, try to download a sample
    if not os.listdir(raw_dir):
        logger.info("No data found in raw directory. Attempting download...")
        # Attempt to download a dataset (logic from T011)
        # For T012, we assume data is already present or downloaded by T011
        # If this script runs alone, it might need to trigger download, but T011 covers that.
        # We proceed with analysis on whatever is in raw_dir.
    
    # Run baseline analysis
    # The function signature in analysis.py now accepts raw_dir and output_path
    results = run_baseline_analysis(raw_dir=raw_dir, output_path=output_path, config=config)
    
    if results:
        logger.info(f"Successfully analyzed {len(results)} datasets.")
        return 0
    else:
        logger.warning("No results generated. Check data availability.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
