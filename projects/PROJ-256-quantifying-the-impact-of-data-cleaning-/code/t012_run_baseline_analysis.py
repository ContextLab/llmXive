import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import setup_logging
from config import Config
from analysis import run_baseline_analysis

def main():
    logger = setup_logging("INFO")
    logger.info("Starting T012: Run Baseline Analysis")
    
    config = Config()
    
    # Get paths from config or defaults
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_path = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(output_path, "baseline_metrics.json")
    
    logger.info(f"Input directory: {raw_dir}")
    logger.info(f"Output file: {output_file}")
    
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    # Run analysis
    # run_baseline_analysis handles both batch (path) and single (df) modes
    # We pass the raw_dir path to trigger batch processing
    success = run_baseline_analysis(raw_dir, output_path=output_file)
    
    if success:
        logger.info("T012 completed successfully. baseline_metrics.json generated.")
        return 0
    else:
        logger.error("T012 failed to generate metrics.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
