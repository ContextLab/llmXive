"""
Task script T012 – Run baseline statistical analysis.

This script loads all CSV files from ``data/raw``, performs a simple
t‑test and linear regression per dataset, and writes a raw JSON output to
``data/processed/baseline_raw_output.json``.

The return value is an exit code (0 for success, 1 for failure) to match
the expectations of the integration test.
"""
import sys
import logging
from pathlib import Path

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis


def main() -> int:
    logger = setup_logging("INFO")
    pin_random_seed(42)

    raw_dir = Path("data/raw")
    output_path = Path("data/processed/baseline_raw_output.json")

    try:
        # Use the flexible ``run_baseline_analysis``; it will write the file.
        run_baseline_analysis(raw_dir, output_path)
        logger.info("Baseline analysis completed successfully.")
        return 0
    except Exception as exc:
        logger.exception("Baseline analysis failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())