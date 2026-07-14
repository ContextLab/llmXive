import os
import sys
import json
import logging
from pathlib import Path
from analysis import run_baseline_analysis
from utils import setup_logging
from config import Config

def main():
    logger = setup_logging("INFO")
    
    # Configuration
    config = Config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("OUTPUT_PATH", "data/processed/baseline_metrics.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    logger.info(f"Starting baseline analysis on {raw_dir}")
    logger.info(f"Output will be written to {output_file}")
    
    success = run_baseline_analysis(raw_dir, output_file, config)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Configuration for analysis
    analysis_config = {
        "outcome_col": config.get("OUTCOME_COL"),
        "group_col": config.get("GROUP_COL"),
        "predictor_col": config.get("PREDICTOR_COL")
    }

    # Check if required columns are defined
    if not analysis_config["outcome_col"]:
        logger.error("Outcome column not defined in config. Cannot run baseline analysis.")
        return 1

    logger.info(f"Running baseline analysis on {raw_dir}")
    logger.info(f"Output will be saved to {output_file}")

    success = run_baseline_analysis(raw_dir, output_file, analysis_config)

    if success:
        logger.info("Baseline analysis completed successfully.")
        return 0
    else:
        logger.error("Baseline analysis failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())