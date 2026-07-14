import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import run_baseline_analysis
from config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run baseline analysis on raw data."""
    config = get_config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("OUTPUT_PATH", "data/processed/baseline_metrics.json")
    
    if not os.path.exists(raw_dir):
        logger.error(f"Raw data directory {raw_dir} does not exist. Run data acquisition first.")
        return 1

    logger.info(f"Running baseline analysis on {raw_dir}")
    
    # Ensure output path is a file
    if not output_file.endswith('.json'):
        output_file = os.path.join(output_file, 'baseline_metrics.json')
    
    success = run_baseline_analysis(raw_dir, output_file, config)
    
    if success:
        logger.info(f"Baseline analysis complete. Output: {output_file}")
        return 0
    else:
        logger.error("Baseline analysis failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
