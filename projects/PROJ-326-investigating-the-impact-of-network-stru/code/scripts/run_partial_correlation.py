"""
Script to run partial correlation analysis.
"""

import argparse
import logging
import sys
from pathlib import Path

from code.src.analysis.partial_correlation import main as partial_correlation_main


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Run partial correlation analysis on simulation results.'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='code/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/analysis/partial_correlation_results.json',
        help='Path to output file'
    )

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting partial correlation analysis...")

    try:
        # Run the analysis
        results = partial_correlation_main()

        logger.info("Partial correlation analysis completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Partial correlation analysis failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())