"""
Monte-Carlo Validation Startup Script (T031)

Runs the Monte-Carlo validation module (T062) as part of pipeline start-up.
Aborts with ERR-801 if any statistical test fails the ≤ 0.005 criterion.

This script is designed to be run before the main audit pipeline to ensure
the statistical validation framework is working correctly.
"""
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.audit.monte_carlo_validation import run_monte_carlo_validation
from code.src.config import set_rng_seed, get_config_summary


def run_monte_carlo_startup_validation(logger: AuditLogger) -> bool:
    """
    Run Monte-Carlo validation as part of pipeline start-up.

    Args:
        logger: The audit logger instance for recording results.

    Returns:
        True if all tests pass (≤ 0.005 difference), False if any fail.
    """
    logger.info("Starting Monte-Carlo validation (T031 startup check)...")

    # Set deterministic seed for reproducibility
    set_rng_seed()
    logger.info(f"Random seed set: {get_config_summary()['seed']}")

    try:
        # Run the full Monte-Carlo validation suite
        results = run_monte_carlo_validation()

        if results is None:
            logger.error("ERR-801: Monte-Carlo validation returned no results")
            return False

        # Check each test result against the ≤ 0.005 criterion
        all_passed = True
        for test_name, result in results.items():
            test_passed = result.get("passed", False)
            diff = result.get("absolute_difference", float("inf"))

            if test_passed:
                logger.info(f"  ✓ {test_name}: passed (diff={diff:.6f} ≤ 0.005)")
            else:
                logger.error(f"  ✗ {test_name}: FAILED (diff={diff:.6f} > 0.005)")
                all_passed = False

        if all_passed:
            logger.info("Monte-Carlo validation PASSED - all tests within tolerance")
            return True
        else:
            logger.error("ERR-801: Monte-Carlo validation FAILED - one or more tests exceeded 0.005 threshold")
            return False

    except Exception as e:
        logger.error(f"ERR-801: Monte-Carlo validation raised exception: {str(e)}")
        return False


def main():
    """
    Entry point for Monte-Carlo validation startup script.

    Exit codes:
        0: All tests passed (≤ 0.005 difference)
        1: One or more tests failed (> 0.005 difference)
        2: Unexpected error during validation
    """
    # Initialize logger
    logger = get_default_logger()
    logger.info("=" * 60)
    logger.info("Monte-Carlo Validation Startup Check (T031)")
    logger.info("=" * 60)

    try:
        # Run validation
        success = run_monte_carlo_startup_validation(logger)

        if success:
            logger.info("Startup validation complete: SUCCESS")
            sys.exit(0)
        else:
            logger.error("Startup validation complete: FAILED - aborting pipeline")
            sys.exit(1)

    except Exception as e:
        logger.error(f"ERR-801: Unexpected error during startup validation: {str(e)}")
        sys.exit(2)


if __name__ == "__main__":
    main()
