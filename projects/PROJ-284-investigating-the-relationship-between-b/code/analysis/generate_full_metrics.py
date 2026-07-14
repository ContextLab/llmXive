import os
import sys
import logging
from pathlib import Path
import pandas as pd

from code.logging_config import get_logger

logger = get_logger(__name__)

def generate_full_metrics(metrics_path: Path, pca_scores_path: Path, output_path: Path):
    """
    Merges individual metrics with PCA factor scores into a single output DataFrame.
    """
    logger.log("generate_full_metrics", metrics=str(metrics_path), pca=str(pca_scores_path))
    
    if not metrics_path.exists():
        logger.log("generate_full_metrics", status="failed", error=f"Metrics file not found: {metrics_path}")
        return
    if not pca_scores_path.exists():
        logger.log("generate_full_metrics", status="failed", error=f"PCA scores file not found: {pca_scores_path}")
        return
    
    df_metrics = pd.read_csv(metrics_path)
    df_pca = pd.read_csv(pca_scores_path)
    
    # Merge on subject_id
    df_full = pd.merge(df_metrics, df_pca, on='subject_id', how='left')
    
    # Save output
    df_full.to_csv(output_path / "full_metrics.csv", index=False)
    
    logger.log("generate_full_metrics", status="completed", path=str(output_path))

def main():
    """
    Main entry point for full metrics generation.
    """
    logger.log("generate_full_metrics_main", status="started")
    
    metrics_path = Path("data/processed/aggregated_metrics.csv")
    pca_scores_path = Path("data/analysis/factor_scores.csv")
    output_path = Path("data/analysis")
    output_path.mkdir(parents=True, exist_ok=True)
    
    generate_full_metrics(metrics_path, pca_scores_path, output_path)

if __name__ == "__main__":
    main()
