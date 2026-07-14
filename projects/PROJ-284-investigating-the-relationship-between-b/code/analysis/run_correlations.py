import os
import sys
import logging
from pathlib import Path

from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main() -> None:
    """Runner script for correlation analysis."""
    logger.log("run_correlations_start")
    try:
        correlations_main()
        logger.log("run_correlations_complete")
    except Exception as e:
        logger.log("run_correlations_error", error=str(e))
        raise

if __name__ == "__main__":
    main()
