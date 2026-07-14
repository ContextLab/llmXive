import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analysis import run_baseline_analysis
from config import get_config
from utils import setup_logging

def main():
    """Main entry point for baseline analysis task."""
    logger = setup_logging("INFO")
    
    logger.info("Starting baseline analysis pipeline")
    
    # Load configuration
    config = get_config()
    
    # Get paths from config or defaults
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("OUTPUT_PATH", "data/processed/baseline_metrics.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    logger.info(f"Starting baseline analysis on {raw_dir}")
    logger.info(f"Output will be written to {output_file}")
    
    success = run_baseline_analysis(raw_dir, output_file, config)
    
    # Check if outcome column is defined
    outcome_column = config.get("OUTCOME_COLUMN")
    if not outcome_column:
        logger.error("Outcome column not defined in config. Cannot run baseline analysis.")
        sys.exit(1)
    
    # Prepare analysis config
    analysis_config = {
        "outcome_column": outcome_column
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Run baseline analysis
    success = run_baseline_analysis(raw_dir, output_file, analysis_config)
    
    if success:
        logger.info(f"Baseline analysis completed successfully. Output: {output_file}")
        sys.exit(0)
    else:
        logger.error("Baseline analysis failed")
        sys.exit(1)

if __name__ == "__main__":
    main()