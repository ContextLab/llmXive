"""
Runner script for correlation analysis (T024).
Invokes the main logic in correlations.py.
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.correlations import main as correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    logger.log("start_run_correlations")
    try:
        correlations_main()
        logger.log("run_correlations_success")
    except Exception as e:
        logger.log("run_correlations_failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
