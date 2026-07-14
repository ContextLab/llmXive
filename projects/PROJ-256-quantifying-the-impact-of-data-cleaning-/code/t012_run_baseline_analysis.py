import os
import sys
import json
import logging
from pathlib import Path
from analysis import run_baseline_analysis
from utils import setup_logging

def main():
    logger = setup_logging("INFO")
    
    # Configuration
    raw_dir = "data/raw"
    output_file = "data/processed/baseline_metrics.json"
    config = {"RANDOM_SEED": 42}

    logger.info(f"Running baseline analysis on {raw_dir}")
    
    success = run_baseline_analysis(raw_dir, output_file, config=config)
    
    if success:
        logger.info(f"Baseline metrics saved to {output_file}")
        return 0
    else:
        logger.error("Baseline analysis failed to produce output.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
