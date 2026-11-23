"""
Script to run sensitivity sweep analysis.
This script is invoked by the main pipeline to generate sensitivity_sweep.json.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.src.analysis.sensitivity import main as sensitivity_main

def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main_wrapper():
    """Wrapper for the sensitivity main function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Running sensitivity sweep via wrapper script...")

    # Simulate command line arguments for the sensitivity module
    sys.argv = [
        'run_sensitivity_sweep',
        '--config', 'code/config.yaml',
        '--output', 'data',
        '--input', 'data/analysis/simulation_results.json'
    ]

    try:
        sensitivity_main()
        logger.info("Sensitivity sweep completed successfully")
    except Exception as e:
        logger.error(f"Sensitivity sweep failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main_wrapper()
