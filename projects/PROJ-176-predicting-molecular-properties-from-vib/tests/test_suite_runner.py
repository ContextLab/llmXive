"""
Test Suite Runner for llmXive Project: Predicting Molecular Properties from Vibrational Spectra.

This script executes the complete test suite defined in the `tests/` directory.
It verifies all acceptance scenarios for User Stories 1-4, including:
- Data alignment and preprocessing contracts (US1)
- Model architecture and training stability (US2)
- Evaluation metrics and statistical significance (US3)
- Independent validation logic (US4)

Usage:
    python tests/test_suite_runner.py
"""

import sys
import os
import argparse
import logging
from pathlib import Path
import unittest

# Add the project root to the path to ensure imports work correctly
# The script is expected to be run from the project root or code directory
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'test_suite_run.log')
    ]
)
logger = logging.getLogger(__name__)

def discover_and_run_tests():
    """
    Discovers and runs all tests in the tests/ directory.
    """
    tests_dir = project_root / 'tests'
    
    if not tests_dir.exists():
        logger.error(f"Tests directory not found at {tests_dir}")
        return False

    logger.info(f"Discovering tests in {tests_dir}...")
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(tests_dir),
        pattern='test_*.py',
        top_level_dir=str(project_root)
    )

    if suite.countTestCases() == 0:
        logger.warning("No test cases found in the tests directory.")
        return True  # Not a failure, just no tests to run

    logger.info(f"Found {suite.countTestCases()} test cases.")

    # Run the suite
    logger.info("Running test suite...")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Log summary
    logger.info("-" * 50)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Skipped: {len(result.skipped)}")
    logger.info("-" * 50)

    if result.failures:
        logger.error("TEST SUITE FAILED (Failures):")
        for test, trace in result.failures:
            logger.error(f"  - {test}")
            logger.error(f"    {trace.split(chr(10))[0]}") # Log first line of traceback

    if result.errors:
        logger.error("TEST SUITE FAILED (Errors):")
        for test, trace in result.errors:
            logger.error(f"  - {test}")
            logger.error(f"    {trace.split(chr(10))[0]}")

    if result.wasSuccessful():
        logger.info("SUCCESS: All acceptance scenarios verified.")
        return True
    else:
        logger.error("FAILURE: One or more acceptance scenarios failed.")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run the full test suite for the molecular properties project.')
    parser.add_argument('--verbose', '-v', action='store_true', help='Increase output verbosity')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    success = discover_and_run_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()