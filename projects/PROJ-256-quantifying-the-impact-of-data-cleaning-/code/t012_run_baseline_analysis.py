import os
import sys
import json
import logging
from pathlib import Path
from analysis import run_baseline_analysis
from utils import setup_logging
from config import get_config

def main():
    setup_logging("INFO")
    logger = logging.getLogger(__name__)

    # Load configuration
    config = get_config()
    
    # Determine paths
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    
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
        logger.warning("Baseline analysis finished but no valid datasets were found.")
        return 0 # Return 0 even if no data, as the script ran correctly

if __name__ == "__main__":
    sys.exit(main())