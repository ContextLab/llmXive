"""
Script to execute regression analysis pipeline.

This script:
1. Filters features (T037b)
2. Verifies inputs (T050)
3. Runs regression (T037a)

Output:
- data/results/filtered_features.json
- data/results/regression_model.json
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.regression import main as regression_main
from src.utils.logging import setup_logger, log_info, log_error, log_critical

def main():
    """Main entry point for regression script."""
    setup_logger('regression')
    
    try:
        log_info("Starting regression analysis pipeline...")
        results = regression_main()
        log_info("Regression analysis completed successfully.")
        return 0
    except Exception as e:
        log_critical(f"Regression analysis failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
