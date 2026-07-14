import os
import sys
import logging
from pathlib import Path

from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)


def main() -> None:
    """
    Runner script for the Correlation Analysis phase (T023a, T023b, T024, T025).
    Executes the full pipeline step.
    """
    logger.log("run_correlations", operation="start", status="running")
    try:
        # Execute the main logic from correlations.py which covers T023a and T023b
        correlations_main()
        
        # Note: T024 (Correlations) and T025 (FDR) are implemented in subsequent tasks/scripts
        # This runner currently focuses on the metric aggregation and PCA output (T023a/b)
        # as per the immediate dependency chain for full_metrics.csv generation.
        
        logger.log("run_correlations", operation="complete", status="success")
    except Exception as e:
        logger.log("run_correlations", operation="fail", error=str(e))
        raise


if __name__ == "__main__":
    main()
