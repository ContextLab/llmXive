import logging
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from logging_config import get_logger

logger = get_logger(__name__)

def load_metrics_data(metrics_csv: str) -> pd.DataFrame:
    """Load metrics from CSV file."""
    if not Path(metrics_csv).exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_csv}")
    df = pd.read_csv(metrics_csv)
    logger.log("load_metrics_data", file=metrics_csv, rows=len(df))
    return df

def compute_and_save_pca(
    metrics_df: pd.DataFrame,
    output_loadings: str = "data/analysis/pca_loadings.csv",
    n_components: int = 2
) -> Tuple[PCA, pd.DataFrame]:
    """
    Compute PCA on network metrics and save loadings.
    
    Input DataFrame must have columns: modularity, global_efficiency, 
    participation_coef, within_module_degree
    
    Output: PCA model and loadings DataFrame with columns component_1, component_2
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    # Filter to only metric columns
    X = metrics_df[metric_cols].values
    
    # Fit PCA
    pca = PCA(n_components=n_components)
    pca.fit(X)
    
    # Create loadings DataFrame
    loadings_data = {}
    for i in range(n_components):
        loadings_data[f'component_{i+1}'] = pca.components_[i]
    
    loadings_df = pd.DataFrame(
        loadings_data,
        index=metric_cols
    )
    
    # Save loadings
    Path(output_loadings).parent.mkdir(parents=True, exist_ok=True)
    loadings_df.to_csv(output_loadings)
    logger.log("compute_and_save_pca", 
              output_file=output_loadings,
              n_components=n_components,
              explained_variance=float(pca.explained_variance_ratio_.sum()))
    
    return pca, loadings_df

def compute_pca_factor_scores(
    metrics_df: pd.DataFrame,
    pca: PCA,
    output_scores: str = "data/analysis/factor_scores.csv"
) -> pd.DataFrame:
    """
    Compute PCA factor scores for each subject.
    
    Returns DataFrame with columns: subject_id, pca_factor_1, pca_factor_2 (if 2 components)
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    X = metrics_df[metric_cols].values
    
    # Transform to get factor scores
    factor_scores = pca.transform(X)
    
    # Create output DataFrame
    scores_data = {'subject_id': metrics_df['subject_id'].values}
    for i in range(pca.n_components_):
        scores_data[f'pca_factor_{i+1}'] = factor_scores[:, i]
    
    scores_df = pd.DataFrame(scores_data)
    
    # Save factor scores
    Path(output_scores).parent.mkdir(parents=True, exist_ok=True)
    scores_df.to_csv(output_scores, index=False)
    logger.log("compute_pca_factor_scores",
              output_file=output_scores,
              n_subjects=len(scores_df),
              n_components=pca.n_components_)
    
    return scores_df

def merge_metrics_and_pca_scores(
    metrics_df: pd.DataFrame,
    factor_scores_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge individual metric columns with PCA factor scores.
    
    Returns DataFrame with all raw metrics AND PCA factors.
    """
    # Merge on subject_id
    merged_df = metrics_df.merge(
        factor_scores_df,
        on='subject_id',
        how='inner'
    )
    
    logger.log("merge_metrics_and_pca_scores",
              input_rows=len(metrics_df),
              output_rows=len(merged_df),
              columns=list(merged_df.columns))
    
    return merged_df

def save_full_metrics(
    full_metrics_df: pd.DataFrame,
    output_file: str = "data/analysis/full_metrics.csv"
) -> None:
    """
    Save full metrics DataFrame (all raw metrics + PCA factors) to CSV.
    
    This ensures FR-005 (FDR on individual metrics) and FR-004 (report generation)
    have access to all data.
    """
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    full_metrics_df.to_csv(output_file, index=False)
    logger.log("save_full_metrics",
              output_file=output_file,
              n_rows=len(full_metrics_df),
              n_columns=len(full_metrics_df.columns),
              columns=list(full_metrics_df.columns))

def compute_and_save_correlation_matrix(
    metrics_df: pd.DataFrame,
    output_file: str = "data/analysis/correlation_matrix.csv"
) -> pd.DataFrame:
    """
    Compute Pearson correlation matrix for all numeric columns.
    """
    numeric_cols = metrics_df.select_dtypes(include=[np.number]).columns
    corr_matrix = metrics_df[numeric_cols].corr()
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    corr_matrix.to_csv(output_file)
    logger.log("compute_and_save_correlation_matrix",
              output_file=output_file,
              shape=corr_matrix.shape)
    
    return corr_matrix

def main(
    metrics_csv: str = "data/processed/metrics.csv",
    output_dir: str = "data/analysis"
) -> None:
    """
    Main pipeline: load metrics, compute PCA, compute factor scores,
    merge everything, and save full_metrics.csv.
    """
    logger.log("main_start", metrics_csv=metrics_csv, output_dir=output_dir)
    
    # Load metrics
    metrics_df = load_metrics_data(metrics_csv)
    
    # Compute PCA and save loadings
    pca, loadings_df = compute_and_save_pca(
        metrics_df,
        output_loadings=f"{output_dir}/pca_loadings.csv"
    )
    
    # Compute factor scores and save
    factor_scores_df = compute_pca_factor_scores(
        metrics_df,
        pca,
        output_scores=f"{output_dir}/factor_scores.csv"
    )
    
    # Merge metrics with PCA scores
    full_metrics_df = merge_metrics_and_pca_scores(metrics_df, factor_scores_df)
    
    # Save full metrics (raw metrics + PCA factors)
    save_full_metrics(full_metrics_df, output_file=f"{output_dir}/full_metrics.csv")
    
    # Also compute and save correlation matrix
    compute_and_save_correlation_matrix(
        full_metrics_df,
        output_file=f"{output_dir}/correlation_matrix.csv"
    )
    
    logger.log("main_complete",
              full_metrics_shape=full_metrics_df.shape,
              output_dir=output_dir)

if __name__ == "__main__":
    main()