import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA

from code.logging_config import get_logger

logger = get_logger(__name__)

def run_pca_on_metrics(metrics_path: Path, output_path: Path):
    """
    Runs PCA on the aggregated metrics and saves factor scores and loadings.
    """
    logger.log("run_pca_on_metrics", path=str(metrics_path))
    
    if not metrics_path.exists():
        logger.log("run_pca_on_metrics", status="failed", error=f"File not found: {metrics_path}")
        return
    
    df = pd.read_csv(metrics_path)
    
    # Select metric columns
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    available_cols = [c for c in metric_cols if c in df.columns]
    
    if not available_cols:
        logger.log("run_pca_on_metrics", status="failed", error="No metric columns found")
        return
    
    X = df[available_cols].fillna(0)
    
    # Run PCA
    pca = PCA(n_components=2)
    scores = pca.fit_transform(X)
    
    # Create output DataFrames
    scores_df = pd.DataFrame(scores, columns=['pca_factor_1', 'pca_factor_2'])
    scores_df.insert(0, 'subject_id', df['subject_id'])
    
    loadings_df = pd.DataFrame(pca.components_, columns=available_cols)
    loadings_df.index = ['component_1', 'component_2']
    
    # Save outputs
    scores_df.to_csv(output_path / "factor_scores.csv", index=False)
    loadings_df.to_csv(output_path / "pca_loadings.csv")
    
    logger.log("run_pca_on_metrics", status="completed", path=str(output_path))

def main():
    """
    Main entry point for PCA runner.
    """
    logger.log("pca_runner_main", status="started")
    
    input_path = Path("data/processed/aggregated_metrics.csv")
    output_path = Path("data/analysis")
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        # Try to generate from raw metrics if aggregated_metrics is missing
        # For now, we assume the pipeline has generated aggregated_metrics.csv
        logger.log("pca_runner_main", status="failed", error=f"Input file not found: {input_path}")
        return
    
    run_pca_on_metrics(input_path, output_path)

if __name__ == "__main__":
    main()
