"""
Runner script for correlation analysis.
"""
import logging
from pathlib import Path
from code.analysis.correlations import main as _correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Entry point for correlation analysis pipeline.
    """
    logger.log("correlation_runner_start", operation="main")
    try:
        _correlations_main()
        logger.log("correlation_runner_complete", status="success")
    except Exception as e:
        logger.log("correlation_runner_error", error=str(e))
        raise

if __name__ == "__main__":
    main()
