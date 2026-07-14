"""
Generate full metrics file combining individual metrics and PCA scores.
This script is invoked by the quickstart run-book to generate full_metrics.csv.
"""
import os
import sys
import logging
from pathlib import Path

import pandas as pd

from code.logging_config import get_logger
from code.analysis.correlations import (
    load_metrics_data,
    generate_full_metrics,
    FACTOR_SCORES_FILE,
    FULL_METRICS_FILE
)

logger = get_logger(__name__)

def main() -> None:
    """
    Main entry point for generating full metrics.
    """
    try:
        logger.log("generate_full_metrics", step="start")
        
        # Load metrics
        df_metrics = load_metrics_data()
        
        # Load PCA scores
        if not Path(FACTOR_SCORES_FILE).exists():
            raise FileNotFoundError(f"PCA factor scores not found at {FACTOR_SCORES_FILE}. "
                                  "Run pca_runner.py first.")
        df_pca = pd.read_csv(FACTOR_SCORES_FILE)
        
        # Generate full metrics
        full_metrics = generate_full_metrics(df_metrics, df_pca)
        
        # Save output
        Path(FULL_METRICS_FILE).parent.mkdir(parents=True, exist_ok=True)
        full_metrics.to_csv(FULL_METRICS_FILE, index=False)
        
        logger.log("generate_full_metrics", 
                 step="completed", 
                 file=FULL_METRICS_FILE, 
                 rows=len(full_metrics))
        
    except Exception as e:
        logger.log("generate_full_metrics", step="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
