import os
import sys
import logging
from pathlib import Path
import pandas as pd
from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main():
    """
    Runner script to generate full_metrics.csv.
    This ensures the file is produced as a side-effect of the analysis pipeline.
    """
    logger.log("generate_full_metrics_runner_start")
    
    # Ensure output directory exists
    os.makedirs("data/analysis", exist_ok=True)
    
    # Run the main correlation logic which generates full_metrics.csv
    try:
        df = correlations_main()
        logger.log("generate_full_metrics_runner_success", rows=len(df))
    except Exception as e:
        logger.log("generate_full_metrics_runner_error", error=str(e))
        raise

if __name__ == "__main__":
    main()
