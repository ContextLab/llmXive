"""Generate full metrics by loading real network metrics and merging with PCA scores."""
import logging
from pathlib import Path
import pandas as pd
from logging_config import get_logger
from analysis.correlations import (
    load_metrics_data,
    compute_and_save_pca,
    compute_pca_factor_scores,
    merge_metrics_and_pca_scores,
    save_full_metrics
)

logger = get_logger(__name__)

def merge_and_save_full_metrics(
    metrics_file: str = "data/analysis/network_metrics.csv",
    pca_loadings_file: str = "data/analysis/pca_loadings.csv",
    factor_scores_file: str = "data/analysis/factor_scores.csv",
    full_metrics_file: str = "data/analysis/full_metrics.csv"
) -> pd.DataFrame:
    """Load metrics, compute PCA, and save full merged dataset.
    
    Args:
        metrics_file: Input file with network metrics
        pca_loadings_file: Output file for PCA loadings
        factor_scores_file: Output file for PCA factor scores
        full_metrics_file: Output file for merged metrics + PCA
    
    Returns:
        Full metrics DataFrame with all columns
    """
    try:
        # Load real metrics data
        metrics_df = load_metrics_data(metrics_file)
        logger.log("loaded_metrics", rows=len(metrics_df), columns=list(metrics_df.columns))
        
        # Compute PCA and save loadings
        pca, loadings_df = compute_and_save_pca(metrics_df, pca_loadings_file, n_components=2)
        
        # Compute factor scores
        factor_scores_df = compute_pca_factor_scores(metrics_df, pca)
        factor_scores_df.to_csv(factor_scores_file, index=False)
        logger.log("saved_factor_scores", file=factor_scores_file)
        
        # Merge and save
        full_metrics_df = merge_metrics_and_pca_scores(metrics_df, factor_scores_df)
        save_full_metrics(full_metrics_df, full_metrics_file)
        
        logger.log("merge_and_save_complete", full_metrics_file=full_metrics_file)
        return full_metrics_df
        
    except Exception as e:
        logger.log("error", operation="merge_and_save_full_metrics", error=str(e))
        raise

def main() -> None:
    """Main entry point."""
    merge_and_save_full_metrics()

if __name__ == "__main__":
    main()
