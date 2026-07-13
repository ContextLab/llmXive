import logging
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from logging_config import get_logger

logger = get_logger(__name__)

def load_metrics_data(metrics_file: str) -> pd.DataFrame:
    """Load network metrics from CSV file.
    
    Args:
        metrics_file: Path to metrics CSV with columns [subject_id, modularity, global_efficiency, participation_coef, within_module_degree]
    
    Returns:
        DataFrame with metrics data
    """
    logger.log("load_metrics_data", metrics_file=metrics_file)
    if not Path(metrics_file).exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}")
    
    df = pd.read_csv(metrics_file)
    logger.log("load_metrics_data_complete", rows=len(df), columns=list(df.columns))
    return df

def compute_and_save_pca(metrics_df: pd.DataFrame, output_file: str, n_components: int = 2) -> Tuple[np.ndarray, np.ndarray]:
    """Compute PCA on network metrics and save loadings.
    
    Args:
        metrics_df: DataFrame with columns [modularity, global_efficiency, participation_coef, within_module_degree]
        output_file: Path to save PCA loadings CSV
        n_components: Number of PCA components (default 2)
    
    Returns:
        Tuple of (loadings array, explained variance ratio)
    """
    logger.log("compute_and_save_pca", n_components=n_components, output_file=output_file)
    
    # Extract metric columns (exclude subject_id if present)
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    X = metrics_df[metric_cols].values
    
    # Fit PCA
    pca = PCA(n_components=n_components)
    pca.fit(X)
    
    # Create loadings DataFrame
    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=[f'component_{i+1}' for i in range(n_components)],
        index=metric_cols
    )
    
    # Save loadings
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    loadings_df.to_csv(output_file)
    logger.log("pca_loadings_saved", file=output_file, shape=loadings_df.shape)
    
    return pca.components_, pca.explained_variance_ratio_

def compute_pca_factor_scores(metrics_df: pd.DataFrame, pca_obj: Optional[PCA] = None, n_components: int = 2) -> pd.DataFrame:
    """Compute PCA factor scores for each subject.
    
    Args:
        metrics_df: DataFrame with columns [subject_id, modularity, global_efficiency, participation_coef, within_module_degree]
        pca_obj: Fitted PCA object (if None, will fit new PCA)
        n_components: Number of components (default 2)
    
    Returns:
        DataFrame with columns [subject_id, pca_factor_1, pca_factor_2, ...]
    """
    logger.log("compute_pca_factor_scores", n_components=n_components)
    
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    X = metrics_df[metric_cols].values
    
    if pca_obj is None:
        pca_obj = PCA(n_components=n_components)
        pca_obj.fit(X)
    
    # Transform data to get factor scores
    scores = pca_obj.transform(X)
    
    # Create output DataFrame
    result_df = pd.DataFrame(
        scores,
        columns=[f'pca_factor_{i+1}' for i in range(n_components)]
    )
    
    # Add subject_id if available
    if 'subject_id' in metrics_df.columns:
        result_df.insert(0, 'subject_id', metrics_df['subject_id'].values)
    
    logger.log("pca_factor_scores_computed", rows=len(result_df), columns=list(result_df.columns))
    return result_df

def save_factor_scores(factor_scores_df: pd.DataFrame, output_file: str) -> None:
    """Save PCA factor scores to CSV.
    
    Args:
        factor_scores_df: DataFrame with factor scores
        output_file: Path to save CSV
    """
    logger.log("save_factor_scores", output_file=output_file)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    factor_scores_df.to_csv(output_file, index=False)
    logger.log("factor_scores_saved", file=output_file, rows=len(factor_scores_df))

def merge_metrics_and_pca_scores(metrics_df: pd.DataFrame, factor_scores_df: pd.DataFrame) -> pd.DataFrame:
    """Merge raw metrics with PCA factor scores.
    
    Args:
        metrics_df: DataFrame with raw network metrics
        factor_scores_df: DataFrame with PCA factor scores
    
    Returns:
        Merged DataFrame with all columns
    """
    logger.log("merge_metrics_and_pca_scores")
    
    # Ensure both have subject_id for merging
    if 'subject_id' not in metrics_df.columns:
        raise ValueError("metrics_df must have 'subject_id' column")
    if 'subject_id' not in factor_scores_df.columns:
        raise ValueError("factor_scores_df must have 'subject_id' column")
    
    merged = metrics_df.merge(factor_scores_df, on='subject_id', how='inner')
    logger.log("metrics_pca_merged", rows=len(merged), columns=list(merged.columns))
    return merged

def save_full_metrics(full_metrics_df: pd.DataFrame, output_file: str) -> None:
    """Save full metrics (raw + PCA) to CSV.
    
    Args:
        full_metrics_df: DataFrame with all metrics and PCA scores
        output_file: Path to save CSV
    """
    logger.log("save_full_metrics", output_file=output_file)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    full_metrics_df.to_csv(output_file, index=False)
    logger.log("full_metrics_saved", file=output_file, rows=len(full_metrics_df), columns=len(full_metrics_df.columns))

def compute_and_save_correlation_matrix(full_metrics_df: pd.DataFrame, output_file: str) -> pd.DataFrame:
    """Compute correlation matrix for all metrics.
    
    Args:
        full_metrics_df: DataFrame with all metrics
        output_file: Path to save correlation matrix
    
    Returns:
        Correlation matrix DataFrame
    """
    logger.log("compute_and_save_correlation_matrix", output_file=output_file)
    
    # Select numeric columns (exclude subject_id)
    numeric_cols = full_metrics_df.select_dtypes(include=[np.number]).columns
    corr_matrix = full_metrics_df[numeric_cols].corr()
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    corr_matrix.to_csv(output_file)
    logger.log("correlation_matrix_saved", file=output_file, shape=corr_matrix.shape)
    return corr_matrix

def main(metrics_file: str = "data/processed/network_metrics.csv",
         pca_loadings_file: str = "data/analysis/pca_loadings.csv",
         factor_scores_file: str = "data/analysis/factor_scores.csv",
         full_metrics_file: str = "data/analysis/full_metrics.csv") -> None:
    """Main PCA pipeline: load metrics, compute PCA, save results.
    
    Args:
        metrics_file: Input metrics CSV path
        pca_loadings_file: Output PCA loadings CSV path
        factor_scores_file: Output factor scores CSV path
        full_metrics_file: Output full metrics CSV path
    """
    logger.log("pca_main_start")
    
    try:
        # Load metrics
        metrics_df = load_metrics_data(metrics_file)
        
        # Compute and save PCA loadings
        pca_components, explained_var = compute_and_save_pca(
            metrics_df, 
            pca_loadings_file,
            n_components=2
        )
        logger.log("pca_explained_variance", var_ratio=list(explained_var))
        
        # Compute and save factor scores
        factor_scores_df = compute_pca_factor_scores(metrics_df, n_components=2)
        save_factor_scores(factor_scores_df, factor_scores_file)
        
        # Merge and save full metrics
        full_metrics_df = merge_metrics_and_pca_scores(metrics_df, factor_scores_df)
        save_full_metrics(full_metrics_df, full_metrics_file)
        
        logger.log("pca_main_complete", 
                  pca_loadings=pca_loadings_file,
                  factor_scores=factor_scores_file,
                  full_metrics=full_metrics_file)
        
    except Exception as e:
        logger.log("pca_main_error", error=str(e))
        raise

if __name__ == "__main__":
    main()