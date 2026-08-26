import os
import sys
import subprocess
import json
import logging
from pathlib import Path

from formatting_utils import main as run_formatting_main
from utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Entry point for running the formatting pipeline.
    """
    logger.info("Starting formatting pipeline execution...")
    
    # Change to project root to ensure relative paths work
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)
    
    try:
        exit_code = run_formatting_main()
        logger.info(f"Formatting pipeline finished with exit code {exit_code}")
        return exit_code
    except Exception as e:
        logger.error(f"Formatting pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
