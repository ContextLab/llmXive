"""
Main orchestration script for the project.

This script supports multiple phases:
- init:   Sets up the environment and prints a confirmation message.
- validate: Runs the clustering validation gate (used by later phases).

The verification for task T001 runs the script with ``--phase init`` and
expects the exact output ``Initialization complete``.
"""

import sys
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the validation logic used in later phases.
# These imports are safe even if the validation phase is not executed.
from validation.validate_clustering import (
    validate_structure,
    validate_data_types,
    validate_consistency,
)
from config import Config

def run_init_phase() -> None:
    """
    Initialization phase – creates required directories (handled by Config)
    and prints a confirmation message.
    """
    # Instantiating Config will create the required data directories.
    _ = Config()
    print("Initialization complete")
    sys.exit(0)

def run_validation_gate() -> bool:
    """
    Executes the Phase 2.5 Validation Gate (used by later tasks).
    Returns True if validation passes, False otherwise.
    """
    config = Config()
    report_path = config.get_clustering_report_path()

    logger.info(f"Starting Validation Gate for: {report_path}")

    if not Path(report_path).exists():
        logger.error(
            f"CRITICAL: Clustering report not found at {report_path}. "
            "Phase 2 may not have completed successfully."
        )
        return False

    try:
        logger.info("Running structural validation...")
        valid, errors = validate_structure(json.load(open(report_path)))
        if not valid:
            logger.error("Structural validation failed.")
            return False

        logger.info("Running data type validation...")
        valid, errors = validate_data_types(json.load(open(report_path)))
        if not valid:
            logger.error("Data type validation failed.")
            return False

        logger.info("Running consistency validation...")
        valid, errors = validate_consistency(json.load(open(report_path)))
        if not valid:
            logger.error("Consistency validation failed.")
            return False

        logger.info("Validation gate PASSED.")
        return True

    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return False

def main() -> None:
    parser = argparse.ArgumentParser(description="Project orchestration script")
    parser.add_argument(
        "--phase",
        type=str,
        required=True,
        choices=["init", "validate"],
        help="Execution phase: 'init' creates the skeleton, 'validate' runs the clustering validation gate."
    )
    args = parser.parse_args()

    if args.phase == "init":
        run_init_phase()
    elif args.phase == "validate":
        success = run_validation_gate()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
