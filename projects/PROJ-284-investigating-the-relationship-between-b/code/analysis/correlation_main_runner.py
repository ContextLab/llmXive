"""
Runner for correlation analysis.
"""
import logging
from pathlib import Path
from code.analysis.correlations import main as _correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    logger.log("correlation_main_runner", step="start")
    _correlations_main()
    logger.log("correlation_main_runner", step="complete")

if __name__ == "__main__":
    main()
