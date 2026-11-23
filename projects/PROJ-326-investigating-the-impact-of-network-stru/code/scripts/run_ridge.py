"""
Script to execute the Ridge Regression analysis (T058).
This script wraps the main logic from code/src/analysis/ridge.py
to be invoked by the pipeline or manually.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.analysis.ridge import main as ridge_main, setup_logging

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
    parser = argparse.ArgumentParser(
        description="Execute Ridge Regression analysis for network metrics vs diffusion rates."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to the configuration file (optional, mostly for consistency)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/analysis/ridge_results.json",
        help="Path for the output JSON file."
    )

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting Ridge Regression with config: {args.config}")
    logger.info(f"Output will be written to: {args.output}")

    # The main logic in ridge.py handles file paths internally based on task specs.
    # We can override the output path if needed, but for now we stick to the standard path
    # defined in the task specification to ensure T037a can find it.
    # The task spec says: Output: data/analysis/ridge_results.json

    try:
        ridge_main()
        logger.info("Ridge Regression completed successfully.")
    except Exception as e:
        logger.error(f"Ridge Regression failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()