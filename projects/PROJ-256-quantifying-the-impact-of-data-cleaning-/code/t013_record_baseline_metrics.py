"""
T013 – Record baseline metrics

This script orchestrates the generation of baseline statistical metrics
(p‑value, 95 % confidence interval, Cohen's d / R²) and writes them to
``data/processed/baseline_metrics.json`` with at least three‑decimal
precision.

It relies on the flexible ``run_baseline_analysis`` function defined in
``code/analysis.py`` and uses the project's shared logging utilities.
"""

import sys
from pathlib import Path

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis


def main() -> int:
    """
    Execute the baseline analysis and ensure the output file exists.
    Returns an exit code suitable for ``sys.exit``.
    """
    # Initialise logging – accept any call signature
    logger = setup_logging(log_level="INFO")

    # Ensure reproducibility across the pipeline
    pin_random_seed(42)

    # Define paths (respecting possible environment overrides via Config)
    raw_dir = Path("data/raw")
    output_file = Path("data/processed/baseline_metrics.json")

    logger.info("Starting baseline metrics recording...")
    success = run_baseline_analysis(raw_dir=raw_dir, output_file=output_file)

    if success and output_file.is_file():
        logger.info(f"Baseline metrics successfully written to {output_file}")
        return 0
    else:
        logger.error("Baseline metrics generation failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())