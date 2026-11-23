"""
Script wrapper to run Ridge Regression analysis (T058).
"""

import argparse
import logging
import sys
from pathlib import Path

from code.src.analysis.ridge import main as ridge_main

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    parser = argparse.ArgumentParser(description="Run Ridge Regression Analysis (T058)")
    parser.add_argument('--config', type=str, default='code/config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--output', type=str, default='data/analysis/ridge_results.json',
                        help='Path to output results file')
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Running Ridge Regression with config: {args.config}")

    # Note: The main logic is in code.src.analysis.ridge
    # We call it directly here. The output path is hardcoded in the module
    # but could be made dynamic if needed.
    exit_code = ridge_main()
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
