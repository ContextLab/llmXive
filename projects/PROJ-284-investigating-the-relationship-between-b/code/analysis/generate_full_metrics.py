"""
Runner script for T023b: Generate Full Metrics.
Invoked by quickstart.md to ensure data/analysis/full_metrics.csv is produced.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.correlations import main as correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Entry point for Full Metrics runner."""
    logger.log("full_metrics_runner_start")
    try:
        # The main function in correlations.py handles both PCA and Full Metrics generation.
        # We call it here to ensure the full pipeline runs if invoked separately.
        result = correlations_main()
        logger.log("full_metrics_runner_complete")
        return result
    except Exception as e:
        logger.log("full_metrics_runner_error", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
