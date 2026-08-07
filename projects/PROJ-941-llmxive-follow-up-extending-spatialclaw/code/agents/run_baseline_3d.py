"""
Helper script to run the 3D Baseline Agent.

This script provides a CLI interface to execute the baseline agent on a dataset
and save the results. It is a wrapper around `baseline_3d.py`.
"""

import os
import sys
import time
import logging
import argparse
from typing import Optional

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.baseline_3d import run_baseline_on_dataset, Baseline3DAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run 3D Baseline Agent and save results.")
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to the input dataset JSON file (e.g., data/raw/synthetic_spatialclaw_v1.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to the output results JSON file (e.g., results/logs/baseline_run.json)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set the logging level'
    )
    return parser.parse_args()


def run_baseline_and_save(input_path: str, output_path: str, log_level: str = 'INFO'):
    """
    Execute the 3D baseline agent and save results.

    Args:
        input_path: Path to input dataset.
        output_path: Path to output results.
        log_level: Logging level.
    """
    logging.getLogger().setLevel(getattr(logging, log_level))

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Starting 3D Baseline execution on {input_path}")
    start_time = time.perf_counter()

    try:
        results = run_baseline_on_dataset(input_path, output_path)
        end_time = time.perf_counter()
        total_time = end_time - start_time

        logger.info(f"Execution completed in {total_time:.2f} seconds.")
        logger.info(f"Processed {len(results)} tasks.")
        logger.info(f"Results saved to {output_path}")

        # Verify output exists
        if os.path.exists(output_path):
            logger.info("Output file verified.")
        else:
            logger.error("Output file was not created.")
            raise RuntimeError("Output file creation failed.")

    except Exception as e:
        logger.error(f"Execution failed: {str(e)}", exc_info=True)
        raise


def main():
    """Main entry point."""
    args = parse_args()
    run_baseline_and_save(args.input, args.output, args.log_level)


if __name__ == '__main__':
    main()