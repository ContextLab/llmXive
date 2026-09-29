"""
main_validation.py

Orchestration script for Phase 2.5: Post-US1 Validation Gate.

This script runs the validation checks defined in T023a (validate_clustering)
and T023b (validate_correlation).

Logic:
1. Run T023a: Validate `data/processed/clustering_report.json`.
2. Run T023b: Validate `data/processed/correlation_results.json` (p-value < 0.05).
3. If either fails, log error and exit with non-zero status (HALT).
4. If both pass, log success and exit with zero status (PROCEED to Phase 4).
"""

import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validation.validate_clustering import main as validate_clustering_main
from validation.validate_correlation import main as validate_correlation_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_validation_gate():
    """
    Executes the Phase 2.5 Validation Gate.
    
    Returns:
        bool: True if validation passes (proceed to Phase 4), False otherwise.
    """
    logger.info("=" * 60)
    logger.info("Starting Phase 2.5: Post-US1 Validation Gate")
    logger.info("=" * 60)
    
    # Step 1: Validate Clustering Report (T023a)
    logger.info("Step 1: Validating clustering report (T023a)...")
    try:
        # The T023a script's main function handles the logic and returns a boolean
        # or raises an exception on failure. We call it directly.
        clustering_valid = validate_clustering_main()
        if not clustering_valid:
            logger.error("Validation FAILED: Clustering report structure or content is invalid.")
            return False
        logger.info("Validation PASSED: Clustering report is valid.")
    except Exception as e:
        logger.error(f"Validation FAILED: Exception during clustering validation: {e}")
        return False
    
    # Step 2: Validate Correlation Results (T023b)
    logger.info("Step 2: Validating correlation results (T023b)...")
    try:
        # The T023b script's main function handles the logic and returns a boolean
        correlation_valid = validate_correlation_main()
        if not correlation_valid:
            logger.error("Validation FAILED: Correlation results are invalid or p-value >= 0.05.")
            return False
        logger.info("Validation PASSED: Correlation results are valid (p < 0.05).")
    except Exception as e:
        logger.error(f"Validation FAILED: Exception during correlation validation: {e}")
        return False
    
    # Step 3: Final Decision
    logger.info("=" * 60)
    logger.info("Phase 2.5 Validation Gate: SUCCESS")
    logger.info("All checks passed. Proceeding to Phase 4 (User Story 2).")
    logger.info("=" * 60)
    return True

def main():
    """Entry point for the orchestration script."""
    success = run_validation_gate()
    if not success:
        logger.error("Validation Gate FAILED. Execution halted. Do not proceed to Phase 4.")
        sys.exit(1)
    else:
        logger.info("Validation Gate PASSED. Ready for Phase 4.")
        sys.exit(0)

if __name__ == "__main__":
    main()