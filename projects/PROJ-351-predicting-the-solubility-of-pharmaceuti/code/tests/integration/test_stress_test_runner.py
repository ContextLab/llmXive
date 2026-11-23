"""
Integration runner for Edge Case Stress Tests (T048).

This script executes the stress tests and validates that the pipeline
adheres to the "Fail Loudly" constraint.
"""
import os
import sys
import unittest
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging for the runner
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stress_test_runner')

def run_stress_tests():
    """
    Run the edge case stress tests and report results.
    """
    logger.info("Starting Edge Case Stress Tests (T048)...")
    
    # Discover and run tests from the test module
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(Path(__file__).parent),
        pattern='test_edge_case_stress.py'
    )

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")

    if result.failures or result.errors:
        logger.error("Stress tests FAILED. The pipeline may not be failing loudly as required.")
        return False
    else:
        logger.info("Stress tests PASSED. The pipeline correctly fails loudly on simulated errors.")
        return True

if __name__ == '__main__':
    success = run_stress_tests()
    sys.exit(0 if success else 1)
