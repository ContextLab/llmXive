"""
Script to record baseline metrics for all raw datasets.

This script is invoked from ``code/main.py`` (as ``record_main``) and
produces ``data/processed/baseline_metrics.json`` using the flexible
``run_baseline_analysis`` function defined in ``code/analysis.py``.
"""

import logging
import sys
from pathlib import Path

from utils import pin_random_seed, setup_logging
from analysis import run_baseline_analysis

def main() -> None:
    """
    Entry point for the baseline‑recording task.

    It pins the random seed, configures logging, and delegates the heavy
    lifting to :func:`run_baseline_analysis`.  The function writes the
    JSON artifact to ``data/processed/baseline_metrics.json``.
    """
    # Initialise reproducibility and logging
    pin_random_seed(42)
    logger = setup_logging(log_level="INFO")
    logger.info("Starting baseline metrics recording")

    raw_dir = Path("data/raw")
    output_file = Path("data/processed/baseline_metrics.json")

    # Run the analysis – the function handles writing the file
    try:
        run_baseline_analysis(str(raw_dir), str(output_file))
        logger.info("Baseline metrics successfully recorded.")
    except Exception as exc:
        logger.exception("Error while recording baseline metrics: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()