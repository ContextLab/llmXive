"""
Wrapper script that executes the baseline analysis and returns an exit code.
"""

import logging
import sys

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis

logger = setup_logging("INFO")


def main() -> int:
    """
    Entry point for the baseline analysis step (T012).

    Returns
    -------
    int
        0 on success, non‑zero on failure.
    """
    logger.info("Starting baseline analysis (T012).")
    # Ensure reproducibility
    pin_random_seed(42)

    # Run the analysis; rely on defaults for paths
    exit_code = run_baseline_analysis()
    if exit_code == 0:
        logger.info("Baseline analysis completed successfully.")
    else:
        logger.error("Baseline analysis failed.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())