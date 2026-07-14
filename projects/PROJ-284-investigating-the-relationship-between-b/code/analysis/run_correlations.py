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
    """
    Runner script for T024 (Correlations) and T025 (FDR).
    Invoked by the main pipeline to ensure data/analysis/correlations.csv is generated.
    """
    logger.log("run_correlations", operation="start")
    try:
        results = correlations_main()
        logger.log("run_correlations", operation="success", rows=len(results))
    except Exception as e:
        logger.log("run_correlations", operation="failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
