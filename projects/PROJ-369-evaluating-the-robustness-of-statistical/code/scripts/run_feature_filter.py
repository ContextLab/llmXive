"""
Script to run feature filtering for regression analysis (T037b).

This script executes the feature filtering logic to exclude
Max_ACF_Lag and spectral density metrics from the regression inputs.

Output: data/results/filtered_features.json
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.regression import main as regression_main
from src.utils.logging import setup_logger


def main():
    """Main entry point for feature filtering script."""
    # Setup logging
    logger = setup_logger('feature_filter', level=logging.INFO)
    
    logger.info("Starting feature filtering (T037b)")
    
    # Run the main regression/feature filtering logic
    exit_code = regression_main()
    
    if exit_code == 0:
        logger.info("Feature filtering completed successfully")
    else:
        logger.error("Feature filtering failed")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
