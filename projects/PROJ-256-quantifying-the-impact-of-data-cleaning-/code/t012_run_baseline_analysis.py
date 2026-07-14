import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis import run_baseline_analysis
from config import Config
from utils import setup_logging

def main():
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("Starting T012: Run Baseline Analysis")
    
    config = Config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(output_dir, "baseline_metrics.json")

    logger.info(f"Input directory: {raw_dir}")
    logger.info(f"Output file: {output_file}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    success = run_baseline_analysis(raw_dir, output_path=output_file)

    if success:
        logger.info("T012 completed successfully.")
        return 0
    else:
        logger.error("T012 failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
