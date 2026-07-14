"""
Correlation Main Runner Script.
Entry point for running the correlation analysis pipeline.
"""
import logging
from pathlib import Path
from code.analysis.correlations import main as _correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Run the correlation analysis pipeline.
    """
    try:
        logger.log("correlation_main_runner", step="start")
        _correlations_main()
        logger.log("correlation_main_runner", step="complete", status="success")
    except Exception as e:
        logger.log("correlation_main_runner", step="error", error=str(e))
        raise

if __name__ == "__main__":
    main()
