"""
Runner for the correlation analysis module (US2).
Ensures PCA, merging, and correlation steps are executed.
"""
import logging
from pathlib import Path
from code.analysis.correlations import main as _correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Entry point for the analysis step.
    """
    logger.log("correlation_main_runner_start")
    try:
        _correlations_main()
        logger.log("correlation_main_runner_complete")
    except Exception as e:
        logger.log("correlation_main_runner_error", error=str(e))
        raise

if __name__ == "__main__":
    main()