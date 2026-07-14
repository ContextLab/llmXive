import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import run_baseline_analysis
from config import Config
from utils import setup_logging

def main():
    setup_logging("INFO")
    logger = logging.getLogger("t012_run_baseline_analysis")
    logger.info("Starting T012: Run Baseline Analysis")

    # Load configuration
    config = Config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(output_file, "baseline_metrics.json")

    logger.info(f"Input directory: {raw_dir}")
    logger.info(f"Output file: {output_file}")

    # Check if raw directory exists and has files
    if not os.path.exists(raw_dir):
        logger.error(f"Input directory {raw_dir} does not exist.")
        return False

    files = [f for f in os.listdir(raw_dir) if f.lower().endswith(('.csv', '.xlsx', '.xls'))]
    if not files:
        logger.error(f"No datasets found in {raw_dir}")
        return False

    # Run analysis
    success = run_baseline_analysis(raw_dir, output_file, config)

    if success:
        logger.info("T012 completed successfully.")
        return True
    else:
        logger.error("T012 failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
