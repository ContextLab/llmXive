import os
import sys
import logging
from pathlib import Path
from src.analysis.validation import main as run_validation
from src.utils.logging import setup_logger

def main():
    """
    Entry point for T015c Validation.
    """
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting T015c Validation Script...")
    
    try:
        run_validation()
        logger.info("T015c Validation completed successfully.")
    except Exception as e:
        logger.error(f"T015c Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()