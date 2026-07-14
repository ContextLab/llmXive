"""
Top‑level pipeline orchestrator.

The script imports the baseline analysis entry point and the baseline
recording script, then executes them sequentially.  It also sets up a
top‑level logger.
"""

import logging
import sys
from pathlib import Path

from utils import pin_random_seed, setup_logging
from t012_run_baseline_analysis import main as baseline_main
from t013_record_baseline_metrics import main as record_main

def main() -> None:
    """
    Execute the full pipeline:
    1. Run the baseline analysis script (may perform additional checks).
    2. Record baseline metrics to the canonical JSON artifact.
    """
    # Global reproducibility
    pin_random_seed(42)

    # Configure a root logger for the whole run
    logger = setup_logging(log_level="INFO")
    logger.info("Pipeline started")

    # Step 1 – run any legacy baseline script
    try:
        baseline_main()
    except Exception as e:
        logger.exception("Baseline script failed: %s", e)
        sys.exit(1)

    # Step 2 – ensure the canonical baseline metrics file exists
    try:
        record_main()
    except Exception as e:
        logger.exception("Recording baseline metrics failed: %s", e)
        sys.exit(1)

    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    main()