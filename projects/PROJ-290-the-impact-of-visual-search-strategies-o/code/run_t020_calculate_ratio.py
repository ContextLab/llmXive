"""
Runner script for Task T020: Calculate Continuous Ratio.

This script executes the logic in code/features/classification.py to compute
the eye-to-mouth fixation ratio and append it to the features file.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging import setup_logging, get_logger
from features.classification import main as classification_main

def main():
    config = get_config()
    log_dir = Path(config.get("paths", {}).get("logs", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = setup_logging(
        name="t020_ratio",
        log_file=log_dir / "t020_ratio.log",
        level=logging.INFO
    )
    
    logger.info("Starting T020 Runner: Calculate Continuous Ratio")
    
    try:
        classification_main(logger)
        logger.info("T020 Runner completed successfully.")
    except Exception as e:
        logger.error(f"T020 Runner failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
