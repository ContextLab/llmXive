"""Create full metrics CSV by merging raw metrics with PCA factor scores.

This script:
1. Loads raw metrics (modularity, global_efficiency, participation_coef, within_module_degree)
2. Computes PCA factor scores
3. Merges them into a single output CSV: data/analysis/full_metrics.csv

Output files:
- data/analysis/pca_loadings.csv: PCA component loadings
- data/analysis/factor_scores.csv: PCA factor scores per subject
- data/analysis/full_metrics.csv: Merged metrics + PCA factors
"""
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from logging_config import get_logger
from analysis.correlations import (
    load_metrics_data,
    compute_and_save_pca,
    compute_pca_factor_scores,
    merge_metrics_and_pca_scores,
    save_full_metrics
)

logger = get_logger(__name__)


def merge_and_save_full_metrics(metrics_csv: str = "data/processed/metrics.csv",
                                output_dir: str = "data/analysis") -> None:
    """Load metrics, compute PCA, and save merged output.
    
    Args:
        metrics_csv: Path to input metrics CSV (from T021/T022)
        output_dir: Directory for output files
    """
    logger.log("merge_and_save_full_metrics", input=metrics_csv, output_dir=output_dir)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load metrics from T021/T022
    if not Path(metrics_csv).exists():
        logger.log("merge_and_save_full_metrics", status="error", 
                  reason=f"Metrics CSV not found: {metrics_csv}")
        raise FileNotFoundError(f"Metrics CSV not found: {metrics_csv}")
    
    metrics_df = load_metrics_data(metrics_csv)
    logger.log("merge_and_save_full_metrics", metrics_loaded=str(metrics_df.shape))
    
    # Compute and save PCA loadings
    pca_loadings_path = f"{output_dir}/pca_loadings.csv"
    compute_and_save_pca(metrics_df, pca_loadings_path)
    logger.log("merge_and_save_full_metrics", pca_loadings_saved=pca_loadings_path)
    
    # Compute and save PCA factor scores
    pca_scores_path = f"{output_dir}/factor_scores.csv"
    pca_scores_df = compute_pca_factor_scores(metrics_df, pca_scores_path)
    logger.log("merge_and_save_full_metrics", pca_scores_saved=pca_scores_path)
    
    # Merge metrics and PCA scores
    merged_df = merge_metrics_and_pca_scores(metrics_df, pca_scores_df)
    logger.log("merge_and_save_full_metrics", merged_shape=str(merged_df.shape))
    
    # Save full metrics
    full_metrics_path = f"{output_dir}/full_metrics.csv"
    save_full_metrics(merged_df, full_metrics_path)
    logger.log("merge_and_save_full_metrics", full_metrics_saved=full_metrics_path)
    
    print(f"✓ Created {full_metrics_path}")
    print(f"  Columns: {', '.join(merged_df.columns)}")
    print(f"  Rows: {len(merged_df)}")


def main() -> None:
    """Main entry point."""
    merge_and_save_full_metrics()


if __name__ == "__main__":
    main()