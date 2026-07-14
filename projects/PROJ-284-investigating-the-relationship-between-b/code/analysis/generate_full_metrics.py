import os
import sys
import logging
from pathlib import Path
import pandas as pd
from code.logging_config import get_logger
from code.analysis.correlations import generate_full_metrics, save_full_metrics

logger = get_logger(__name__)

def main():
    """
    Specific runner for T023b: Generate and Save Full Metrics.
    """
    logger.log("generate_full_metrics_runner_start")
    try:
        df = generate_full_metrics()
        save_full_metrics(df)
        logger.log("generate_full_metrics_runner_success", path="data/analysis/full_metrics.csv")
    except Exception as e:
        logger.log("generate_full_metrics_runner_error", error=str(e))
        raise

if __name__ == "__main__":
    main()
