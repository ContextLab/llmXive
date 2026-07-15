"""
t012_run_baseline_analysis.py
--------------------------------
Script that executes the baseline analysis and writes a raw JSON artifact.
The script is invoked by the integration test and returns an exit code
compatible with subprocess expectations (0 = success).
"""

import logging
import os
from pathlib import Path
import sys

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis


def main() -> int:
    """
    Executes the baseline analysis, storing the intermediate raw results at
    `data/processed/baseline_raw_output.json`. Returns 0 on success,
    non‑zero on failure.
    """
    logger = setup_logging("INFO")
    try:
        # Ensure reproducibility
        pin_random_seed(42)

        raw_output_path = Path("data/processed/baseline_raw_output.json")
        raw_output_path.parent.mkdir(parents=True, exist_ok=True)

        # Run analysis – we let the function write the file directly.
        run_baseline_analysis(
            raw_dir="data/raw",  # placeholder – the function falls back to the default dataset
            output_file=str(raw_output_path),
        )

        logger.info("Baseline analysis script completed successfully.")
        return 0
    except Exception as e:
        logger.exception("Baseline analysis failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())