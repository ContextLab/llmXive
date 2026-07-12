"""
Monte-Carlo Validation Startup Hook (Task T031).

This module ensures that the Monte-Carlo validation (T062) is executed
as part of the pipeline start-up sequence. It imports and runs the
`run_monte_carlo_validation` function from the T062 module.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from code.src.audit.monte_carlo_validation import run_monte_carlo_validation
from code.src.utils.logger import get_default_logger, AuditLogger

logger: logging.Logger = get_default_logger(__name__)
audit_logger: AuditLogger = AuditLogger(logger)

def run_startup_validation() -> bool:
    """
    Executes the Monte-Carlo validation suite upon pipeline start-up.

    This function wraps the T062 validation logic to ensure it runs
    before the main audit pipeline proceeds. It logs the outcome and
    returns a boolean indicating success or failure.

    Returns:
        bool: True if validation passes, False otherwise.
    """
    logger.info("Starting Monte-Carlo validation as part of pipeline start-up (T031).")
    try:
        # Run the validation from T062
        # This function is expected to return a dict with results or raise on failure
        result = run_monte_carlo_validation()
        
        if not result:
            audit_logger.error("ERR-620", "Monte-Carlo validation returned an empty or invalid result.")
            return False

        # Check for specific failure indicators if the result dict contains them
        if isinstance(result, dict):
            if result.get("status") == "failed":
                audit_logger.error("ERR-621", "Monte-Carlo validation failed during execution.")
                return False
            
            # Log summary of validation
            logger.info(f"Monte-Carlo validation completed. Tests passed: {result.get('tests_passed', 0)}/{result.get('total_tests', 0)}")
            return True
        
        # If it returns True directly (common pattern for success)
        if result is True:
            logger.info("Monte-Carlo validation passed successfully.")
            return True

        # Fallback for unexpected return types
        logger.warning("Unexpected return type from Monte-Carlo validation.")
        return False

    except Exception as e:
        audit_logger.error("ERR-622", f"Monte-Carlo validation startup failed with exception: {e}")
        return False

def main() -> int:
    """
    Entry point for running the startup validation as a script.
    Returns 0 on success, 1 on failure.
    """
    success = run_startup_validation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
