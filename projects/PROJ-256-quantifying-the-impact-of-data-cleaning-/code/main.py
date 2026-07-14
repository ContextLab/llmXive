"""
Main entry point for the Quantifying Data Cleaning Impact pipeline.

The script orchestrates the high‑level steps:
1. Baseline analysis on raw data.
2. Re‑analysis of cleaned variants.
3. Generation of permutation‑based null datasets for FPR estimation (T032).
"""

import logging
import sys
from pathlib import Path

from utils import setup_logging, pin_random_seed
from t012_run_baseline_analysis import main as baseline_main
from t023_reanalyze_cleaned_variants import main as cleaned_main
from t032_permutation_null_fpr import main as null_fpr_main

def main() -> None:
    """
    Execute the pipeline sequentially.
    """
    logger = setup_logging(log_level="INFO")
    logger.info("=== Pipeline start ===")

    # 1. Baseline analysis on raw datasets
    try:
        logger.info("Running baseline analysis (raw data).")
        baseline_main()
    except Exception as exc:
        logger.error(f"Baseline analysis failed: {exc}")
        sys.exit(1)

    # 2. Re‑analysis of cleaned variants
    try:
        logger.info("Running cleaned‑variant re‑analysis.")
        cleaned_main()
    except Exception as exc:
        logger.error(f"Cleaned‑variant analysis failed: {exc}")
        sys.exit(1)

    # 3. Permutation‑based null FPR estimation (Task T032)
    try:
        logger.info("Generating permutation null datasets for FPR estimation.")
        null_fpr_main()
    except Exception as exc:
        logger.error(f"Null FPR generation failed: {exc}")
        sys.exit(1)

    logger.info("=== Pipeline completed successfully ===")

if __name__ == "__main__":
    # Ensure reproducibility across the whole pipeline
    pin_random_seed(42)
    main()