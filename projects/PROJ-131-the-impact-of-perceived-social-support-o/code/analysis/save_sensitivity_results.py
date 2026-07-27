"""
Save Sensitivity Analysis Results

This module orchestrates the comparison between baseline regression results
and sensitivity analysis results (continuous harassment, platform stratification).
It extracts interaction coefficients, computes shifts, and saves the summary
to data/results/sensitivity_analysis.csv.

It relies on code/analysis/sensitivity_compare.py for the comparison logic.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure the parent directory is in the path for relative imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.sensitivity_compare import main as compare_main

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for saving sensitivity analysis results.
    
    1. Runs the comparison logic (loads baseline, loads sensitivity, compares).
    2. Saves the resulting comparison table to data/results/sensitivity_analysis.csv.
    """
    logger.info("Starting sensitivity analysis result saving process.")
    
    # The compare_main function handles loading, comparing, and saving the CSV.
    # We delegate to it to ensure consistency with the comparison logic.
    try:
        compare_main()
        logger.info("Sensitivity analysis results successfully saved to data/results/sensitivity_analysis.csv")
        return True
    except Exception as e:
        logger.error(f"Failed to save sensitivity analysis results: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    success = main()
    sys.exit(0 if success else 1)