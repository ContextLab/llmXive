"""
T012: Implement baseline analysis in code/analysis.py using scipy.stats (t-tests)
and statsmodels (linear regression).
"""
import os
import sys
import json
import logging
from pathlib import Path
from analysis import run_baseline_analysis
from utils import setup_logging

logger = setup_logging("INFO")

def main():
    """Main entry point for T012."""
    logger.info("Starting T012: Baseline Analysis")
    
    raw_dir = "data/raw"
    output_file = "data/processed/baseline_metrics.json"
    config = {}
    
    if not os.path.exists(raw_dir):
        logger.error(f"Raw data directory not found: {raw_dir}")
        return
    
    # Run baseline analysis
    success = run_baseline_analysis(raw_dir, output_file, config)
    
    if success:
        logger.info("Baseline analysis completed successfully")
    else:
        logger.error("Baseline analysis failed")

if __name__ == "__main__":
    main()
