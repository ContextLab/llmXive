"""
Script to execute the T048 Edge Case Stress Test.

This script simulates network failures and RDKit parsing errors to verify
that the pipeline fails loudly without synthetic fallbacks.

Usage:
    python code/tests/run_t048_stress_test.py
"""
import os
import sys
import unittest
import logging
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('T048_StressTest')

def main():
    logger.info("=" * 60)
    logger.info("Starting T048: Edge Case Stress Test")
    logger.info("Verifying 'Fail Loudly' behavior for Network and RDKit errors.")
    logger.info("=" * 60)

    # Load the test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Import test modules dynamically to ensure they are found
    try:
        from tests.test_edge_case_stress import TestNetworkFailure, TestRDKitParsingErrors
        suite.addTests(loader.loadTestsFromTestCase(TestNetworkFailure))
        suite.addTests(loader.loadTestsFromTestCase(TestRDKitParsingErrors))
    except ImportError as e:
        logger.error(f"Failed to import test cases: {e}")
        logger.error("Ensure code/tests/test_edge_case_stress.py exists and is correct.")
        return 1

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    logger.info("-" * 60)
    logger.info("Stress Test Summary:")
    logger.info(f"  Total Tests: {result.testsRun}")
    logger.info(f"  Failures: {len(result.failures)}")
    logger.info(f"  Errors: {len(result.errors)}")
    logger.info("-" * 60)

    if result.failures:
        logger.warning("Some tests failed. Check the output above for details.")
        for test, trace in result.failures:
            logger.warning(f"Failure in {test}: {trace.split(chr(10))[0]}")
    
    if result.errors:
        logger.warning("Some tests encountered errors.")
        for test, trace in result.errors:
            logger.warning(f"Error in {test}: {trace.split(chr(10))[0]}")

    if result.wasSuccessful():
        logger.info("SUCCESS: All stress tests passed. The pipeline fails loudly as required.")
        return 0
    else:
        logger.error("FAILURE: The pipeline did not behave as expected under stress.")
        return 1

if __name__ == '__main__':
    sys.exit(main())