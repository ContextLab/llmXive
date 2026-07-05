"""
Runner script for Task T039: Versioning.
Executes the versioning module to generate SHA hashes for all project artifacts.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.versioning import main
from src.utils.logging import setup_logger

def main_wrapper():
    """Wrapper to ensure logging is configured before running versioning."""
    logger = setup_logger("runner_t039")
    logger.info("Executing T039: Generate version hashes...")
    
    try:
        exit_code = main()
        logger.info(f"T039 execution finished with code {exit_code}")
        return exit_code
    except Exception as e:
        logger.critical(f"T039 execution failed with exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())
