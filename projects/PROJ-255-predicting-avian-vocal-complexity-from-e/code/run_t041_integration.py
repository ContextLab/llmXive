"""
Runner script for T041: Integration Test on Representative Subset.

Executes the integration test defined in tests/integration/test_e2e_flow.py.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.utils.logging import setup_logger
from tests.integration.test_e2e_flow import main as run_integration_test

def main():
    logger = setup_logger("run_t041", level=logging.INFO)
    logger.info("Starting T041 Integration Test Runner...")
    
    try:
        exit_code = run_integration_test()
        if exit_code == 0:
            logger.info("T041 Runner: Success")
        else:
            logger.error("T041 Runner: Failed")
        return exit_code
    except Exception as e:
        logger.exception(f"T041 Runner crashed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())