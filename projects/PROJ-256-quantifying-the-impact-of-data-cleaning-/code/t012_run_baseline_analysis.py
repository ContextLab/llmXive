import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from utils import setup_logging
from config import get_config
from analysis import run_baseline_analysis

def main():
    """
    Wrapper script to run T012 baseline analysis.
    Reads config, runs analysis, and exits.
    """
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    logger.info("Starting T012: Run Baseline Analysis")

    config = get_config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("OUTPUT_PATH", "data/processed/baseline_metrics.json")

    logger.info(f"Input directory: {raw_dir}")
    logger.info(f"Output file: {output_file}")

    if not os.path.exists(raw_dir):
        logger.error(f"Input directory does not exist: {raw_dir}")
        sys.exit(1)

    success = run_baseline_analysis(raw_dir, output_file, config=config)
    if success:
        logger.info("T012 completed successfully.")
        sys.exit(0)
    else:
        logger.error("T012 failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
