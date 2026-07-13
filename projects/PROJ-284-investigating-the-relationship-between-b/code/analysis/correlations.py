import logging
from pathlib import Path
from typing import Optional
import pandas as pd
from sklearn.decomposition import PCA
from logging_config import get_logger

logger = get_logger(__name__)


def load_metrics_data(metrics_file: str) -> pd.DataFrame:
    """Load metrics data from CSV file."""
    if not Path(metrics_file).exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}")
    df = pd.read_csv(metrics_file)
    logger.info(f"Loaded metrics data from {metrics_file}: {len(df)} rows")
    return df


def compute_and_save_pca(
    metrics_df: pd.DataFrame,
    output_file: str,
    n_components: int = 2
) -> tuple:
    """Compute PCA on network metrics and save loadings."""
    metric_cols = [col for col in metrics_df.columns 
                  if col in ['modularity', 'global_efficiency', 
                             'participation_coef', 'within_module_degree']]
    
    if not metric_cols:
        raise ValueError("No valid metric columns found in data")
    
    X = metrics_df[metric_cols].values
    pca = PCA(n_components=n_components)
    pca.fit(X)
    
    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=[f'component_{i+1}' for i in range(n_components)],
        index=metric_cols
    )
    
    loadings_df.to_csv(output_file)
    logger.info(f"PCA loadings saved to {output_file}")
    
    return pca, loadings_df


def compute_pca_factor_scores(
    metrics_df: pd.DataFrame,
    pca: PCA
) -> pd.DataFrame:
    """Compute PCA factor scores for each subject."""
    metric_cols = [col for col in metrics_df.columns 
                  if col in ['modularity', 'global_efficiency', 
                             'participation_coef', 'within_module_degree']]
    
    X = metrics_df[metric_cols].values
    scores = pca.transform(X)
    
    scores_df = pd.DataFrame(
        scores,
        columns=[f'pca_factor_{i+1}' for i in range(scores.shape[1])]
    )
    
    if 'subject_id' in metrics_df.columns:
        scores_df.insert(0, 'subject_id', metrics_df['subject_id'].values)
    
    return scores_df


def merge_metrics_and_pca_scores(
    metrics_df: pd.DataFrame,
    pca_scores_df: pd.DataFrame
) -> pd.DataFrame:
    """Merge individual metrics with PCA factor scores."""
    if 'subject_id' in metrics_df.columns and 'subject_id' in pca_scores_df.columns:
        merged = pd.merge(metrics_df, pca_scores_df, on='subject_id', how='inner')
    else:
        merged = pd.concat([metrics_df.reset_index(drop=True), 
                           pca_scores_df.reset_index(drop=True)], axis=1)
    
    return merged


def save_full_metrics(
    full_metrics_df: pd.DataFrame,
    output_file: str
) -> None:
    """Save full metrics (raw metrics + PCA factors) to CSV."""
    full_metrics_df.to_csv(output_file, index=False)
    logger.info(f"Full metrics saved to {output_file}: {len(full_metrics_df)} rows, "
               f"{len(full_metrics_df.columns)} columns")


def compute_and_save_correlation_matrix(
    full_metrics_df: pd.DataFrame,
    output_file: str
) -> pd.DataFrame:
    """Compute correlation matrix for all metrics and save."""
    metric_cols = [col for col in full_metrics_df.columns 
                  if col not in ['subject_id', 'age', 'sex', 'fd']]
    
    corr_matrix = full_metrics_df[metric_cols].corr()
    corr_matrix.to_csv(output_file)
    logger.info(f"Correlation matrix saved to {output_file}")
    
    return corr_matrix


def main(
    metrics_file: str = "data/processed/metrics.csv",
    pca_loadings_file: str = "data/analysis/pca_loadings.csv",
    factor_scores_file: str = "data/analysis/factor_scores.csv",
    full_metrics_file: str = "data/analysis/full_metrics.csv"
) -> None:
    """Main pipeline: load metrics, compute PCA, merge, and save full metrics."""
    logger.info("Starting correlation analysis pipeline")
    
    try:
        # Load metrics
        metrics_df = load_metrics_data(metrics_file)
        
        # Compute PCA
        pca, loadings_df = compute_and_save_pca(
            metrics_df,
            pca_loadings_file,
            n_components=2
        )
        
        # Compute factor scores
        factor_scores_df = compute_pca_factor_scores(metrics_df, pca)
        factor_scores_df.to_csv(factor_scores_file, index=False)
        logger.info(f"Factor scores saved to {factor_scores_file}")
        
        # Merge metrics and PCA scores
        full_metrics_df = merge_metrics_and_pca_scores(metrics_df, factor_scores_df)
        
        # Save full metrics
        save_full_metrics(full_metrics_df, full_metrics_file)
        
        logger.info("Correlation analysis pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Error in correlation analysis pipeline: {str(e)}")
        raise


if __name__ == "__main__":
    main()