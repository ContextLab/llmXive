"""
Runner script for T048 Edge Case Stress Test.
Executes the integration tests and ensures the failure_test_log.txt is generated.
"""
import os
import sys
import unittest
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.test_failure_modes import run_all_tests
from code.utils.ensure_results_dir import ensure_results_directory

def main():
    """Main entry point for the stress test runner."""
    # Ensure results directory exists
    results_dir = ensure_results_directory()
    log_file = results_dir / "failure_test_log.txt"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting T048 Edge Case Stress Test. Log file: {log_file}")
    
    # Run the tests
    result = run_all_tests()
    
    # Verify log file creation
    if log_file.exists():
        logger.info(f"SUCCESS: Log file {log_file} generated.")
        # Print log content for verification
        with open(log_file, 'r') as f:
            logger.info("Log content:\n" + f.read())
    else:
        logger.error("FAILURE: Log file was not generated.")
        sys.exit(1)
        
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()