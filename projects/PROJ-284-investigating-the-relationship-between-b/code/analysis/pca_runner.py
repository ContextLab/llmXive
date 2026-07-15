import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from code.logging_config import get_logger
from code.analysis.correlations import run_pca_on_metrics, load_metrics_data

logger = get_logger(__name__)

def main() -> None:
    """
    Runner script for T023a to ensure execution from command line.
    Executes PCA on aggregated metrics and writes outputs to disk.
    """
    logger.log("pca_runner_start", operation="PCA Runner")
    
    input_file = "data/processed/aggregated_metrics.csv"
    if not Path(input_file).exists():
        logger.log("pca_runner_failed", reason=f"Input file {input_file} not found. "
                 "Run T021/T022 first to generate aggregated metrics.")
        raise FileNotFoundError(f"Input file {input_file} not found.")

    try:
        df = load_metrics_data(input_file)
        logger.log("pca_runner_loaded", subjects=len(df))
        
        # Execute PCA
        loadings, scores = run_pca_on_metrics(df)
        
        logger.log("pca_runner_success", 
                   output_loadings="data/analysis/pca_loadings.csv",
                   output_scores="data/analysis/factor_scores.csv")
        
    except Exception as e:
        logger.log("pca_runner_error", error=str(e))
        raise

if __name__ == "__main__":
    main()
