"""
Runner script for Task T040: Update state file with artifact hashes.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.state_updater import main
from src.utils.logging import setup_logger

def main_wrapper():
    logger = setup_logger(__name__)
    logger.info("Starting Task T040: State Update")
    exit_code = main()
    if exit_code == 0:
        logger.info("Task T040 finished successfully.")
    else:
        logger.error("Task T040 failed.")
    return exit_code

if __name__ == "__main__":
    sys.exit(main_wrapper())
