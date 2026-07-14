"""
Runner script for correlation analysis (T024, T025, T023a, T023b).
This script is invoked by the main pipeline to execute the analysis step.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main():
    """Execute the correlation analysis pipeline."""
    logger.log("start_correlation_pipeline")
    try:
        # Execute the main logic from correlations.py which covers T023a and T023b
        correlations_main()
        logger.log("correlation_pipeline_success")
    except Exception as e:
        logger.log("correlation_pipeline_failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
