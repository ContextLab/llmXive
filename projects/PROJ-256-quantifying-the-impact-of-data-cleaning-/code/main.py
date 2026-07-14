"""
Project entry point – orchestrates the full pipeline: cleaning, analysis,
and reporting. Data flows sequentially through these stages.
"""
import logging
import sys
from pathlib import Path

from utils import setup_logging

def main() -> None:
    """
    Minimal pipeline runner.
    - Initialise logging.
    - Execute the permutation null FPR generation script.
    """
    logger = setup_logging("INFO")
    logger.info("=== Starting pipeline (main) ===")

    # Import locally to avoid circular imports during module load.
    try:
        from t032_permutation_null_fpr import main as null_fpr_main
    except Exception as exc:
        logger.error("Failed to import permutation null script: %s", exc)
        sys.exit(1)

    try:
        null_fpr_main()
    except Exception as exc:
        logger.error("Permutation null FPR generation failed: %s", exc)
        sys.exit(1)

    logger.info("=== Pipeline completed successfully ===")

if __name__ == "__main__":
    main()