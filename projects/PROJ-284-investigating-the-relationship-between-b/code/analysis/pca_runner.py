import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

from code.logging_config import get_logger
from code.analysis.correlations import run_pca_on_metrics, save_pca_outputs

logger = get_logger(__name__)

def main():
    """
    Runner for PCA analysis (T023a).
    Reads: data/analysis/aggregated_metrics.csv
    Outputs: data/analysis/pca_loadings.csv, data/analysis/factor_scores.csv
    """
    input_path = Path("data/analysis/aggregated_metrics.csv")
    loadings_path = Path("data/analysis/pca_loadings.csv")
    scores_path = Path("data/analysis/factor_scores.csv")

    if not input_path.exists():
        logger.log("pca_runner", status="failed", reason=f"Input {input_path} not found. Run T022 first.")
        sys.exit(1)

    logger.log("pca_runner", status="starting", input=str(input_path))

    # Load data
    df = pd.read_csv(input_path)
    
    # Select numeric columns for PCA
    # Assuming columns: modularity, global_efficiency, participation_coef, within_module_degree
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    available_cols = [c for c in metric_cols if c in df.columns]
    
    if len(available_cols) < 2:
        logger.log("pca_runner", status="failed", reason="Not enough metrics for PCA")
        sys.exit(1)

    X = df[available_cols].values
    
    # Run PCA
    loadings, scores = run_pca_on_metrics(X, n_components=2)
    
    # Save outputs
    save_pca_outputs(loadings, scores, available_cols, loadings_path, scores_path)
    
    logger.log("pca_runner", status="success", loadings=str(loadings_path), scores=str(scores_path))

if __name__ == "__main__":
    main()
