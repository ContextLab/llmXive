import os
import sys
import logging
from pathlib import Path

from src.data.profiles import main
from src.utils import setup_logging


def main_wrapper() -> int:
    """
    Wrapper for the profiling main function with logging setup.
    
    Returns:
        Exit code from main().
    """
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Running profiling pipeline...")
        return main()
    except Exception as e:
        logger.error(f"Profiling pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main_wrapper())
