"""
Main orchestration script for Phase 2.5: Validation Gate.

This script runs the clustering validation (T023a).
- If validation fails: Halts execution, logs error, and exits with code 1.
- If validation succeeds: Logs success and exits with code 0, allowing Phase 3 to proceed.
"""
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the validation logic from the existing module (T023a)
# API surface: from validation.validate_clustering import validate_structure, validate_data_types, validate_consistency, main
from validation.validate_clustering import validate_structure, validate_data_types, validate_consistency
from config import Config


def run_validation_gate():
    """
    Executes the Phase 2.5 Validation Gate.
    Returns True if validation passes, False otherwise.
    """
    config = Config()
    report_path = config.CLUSTERING_REPORT_PATH

    logger.info(f"Starting Phase 2.5 Validation Gate for: {report_path}")

    if not Path(report_path).exists():
        logger.error(f"CRITICAL: Clustering report not found at {report_path}. Phase 2 (T022) may not have completed successfully.")
        return False

    # Run the three validation checks defined in T023a
    try:
        logger.info("Running structural validation...")
        if not validate_structure(report_path):
            logger.error("CRITICAL: Structural validation failed.")
            return False

        logger.info("Running data type validation...")
        if not validate_data_types(report_path):
            logger.error("CRITICAL: Data type validation failed.")
            return False

        logger.info("Running consistency validation...")
        if not validate_consistency(report_path):
            logger.error("CRITICAL: Consistency validation failed.")
            return False

        logger.info("Phase 2.5 Validation Gate PASSED. Proceeding to Phase 3.")
        return True

    except Exception as e:
        logger.error(f"CRITICAL: An unexpected error occurred during validation: {e}")
        return False


def main():
    """
    Entry point for the orchestration script.
    """
    success = run_validation_gate()

    if success:
        logger.info("Validation successful. Pipeline can proceed to Phase 3.")
        sys.exit(0)
    else:
        logger.error("Validation failed. Pipeline halted. Do not proceed to Phase 3.")
        sys.exit(1)


if __name__ == "__main__":
    main()