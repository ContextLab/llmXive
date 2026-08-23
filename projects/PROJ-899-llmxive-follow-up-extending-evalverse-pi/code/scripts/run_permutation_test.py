import os
import sys
import logging
from pathlib import Path
from src.models.metrics import main
from src.utils import setup_logging

def main_wrapper():
    """Wrapper for the permutation test script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    try:
        main()
        return 0
    except Exception as e:
        logger.error(f"Permutation test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())