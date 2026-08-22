"""
Test runner for the llmXive Antibiotic Resistance Pipeline.
Executes the full test suite including contract, unit, and integration tests.
"""
import sys
import os
import logging
import argparse
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging import get_logger, init_pipeline_logging

def main():
    # Initialize logging
    log_path = project_root / "logs" / "test_run.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = init_pipeline_logging(
        name="test_runner",
        log_file=log_path,
        level=logging.INFO
    )

    logger.info("=" * 80)
    logger.info("Starting Full Test Suite for Antibiotic Resistance Pipeline")
    logger.info("=" * 80)

    # Import pytest programmatically
    try:
        import pytest
    except ImportError:
        logger.error("pytest is not installed. Please install it via: pip install pytest")
        return 1

    # Define test paths based on project structure
    test_dirs = [
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]
    
    # Filter to existing directories
    existing_paths = []
    for d in test_dirs:
        full_path = project_root / d
        if full_path.exists():
            existing_paths.append(str(full_path))
            logger.info(f"Found test directory: {d}")
        else:
            logger.warning(f"Test directory not found: {d} (skipping)")

    if not existing_paths:
        logger.error("No test directories found. Cannot run tests.")
        return 1

    # Build pytest arguments
    pytest_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback
        "--strict-markers",
        "--color=yes",
        "--junit-xml=" + str(project_root / "tests" / "results" / "junit.xml"),
    ]
    
    # Add specific test directories
    pytest_args.extend(existing_paths)

    logger.info(f"Running pytest with arguments: {pytest_args}")
    logger.info("-" * 80)

    # Run pytest
    exit_code = pytest.main(pytest_args)

    logger.info("-" * 80)
    if exit_code == 0:
        logger.info("SUCCESS: All tests passed.")
    elif exit_code == 1:
        logger.error("FAILURE: Some tests failed.")
    elif exit_code == 2:
        logger.error("INTERRUPTED: Test run interrupted (e.g., KeyboardInterrupt).")
    else:
        logger.error(f"ERROR: pytest exited with code {exit_code}.")

    return exit_code

if __name__ == "__main__":
    sys.exit(main())
