import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from utils import setup_logging, pin_random_seed
from config import Config, get_config
from analysis import run_baseline_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Script to run baseline analysis on raw datasets.
    Produces: data/processed/baseline_metrics.json
    """
    logger = setup_logging("INFO")
    logger.info("Starting T012: Baseline Analysis")
    
    config = get_config()
    pin_random_seed(config.get("RANDOM_SEED", 42))
    
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("OUTPUT_PATH", "data/processed/baseline_metrics.json")
    
    if not os.path.exists(raw_dir):
        logger.error(f"Raw data directory {raw_dir} does not exist. Run T011 first.")
        sys.exit(1)
    
    logger.info(f"Analyzing datasets in {raw_dir}")
    
    try:
        success = run_baseline_analysis(raw_dir, output_file, config=config)
        if success:
            logger.info(f"Successfully wrote baseline metrics to {output_file}")
            # Verify file exists
            if os.path.exists(output_file):
                logger.info("Output file verified.")
            else:
                logger.error("Output file was not created despite success flag.")
                sys.exit(1)
        else:
            logger.error("Analysis returned failure.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()