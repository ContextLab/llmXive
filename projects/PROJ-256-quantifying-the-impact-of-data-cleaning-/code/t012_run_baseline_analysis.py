import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import run_baseline_analysis
from config import get_config

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    config = get_config()
    
    # Determine paths from config or defaults
    if hasattr(config, 'get'):
        raw_dir = config.get("RAW_DATA_PATH", "data/raw")
        output_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    else:
        raw_dir = "data/raw"
        output_dir = "data/processed"

    output_file = os.path.join(output_dir, "baseline_metrics.json")

    logger.info(f"Running baseline analysis on directory: {raw_dir}")
    
    success = run_baseline_analysis(raw_dir, output_file, config)
    
    if success:
        logger.info(f"Successfully wrote baseline metrics to {output_file}")
        return 0
    else:
        logger.warning(f"Baseline analysis finished but no data was processed or output failed.")
        # Return 0 anyway as the script ran, just no data
        return 0

if __name__ == "__main__":
    sys.exit(main())
