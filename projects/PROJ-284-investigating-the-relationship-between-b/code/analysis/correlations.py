import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import numpy as np
from scipy import stats
from code.logging_config import get_logger
from code.utils.memory_monitor import calculate_batch_size

logger = get_logger(__name__)


def load_metrics_data(metrics_path: str) -> pd.DataFrame:
    """Load aggregated metrics from CSV."""
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    df = pd.read_csv(metrics_path)
    logger.log("load_metrics_data", path=metrics_path, rows=len(df))
    return df


def run_pca(metrics_df: pd.DataFrame, n_components: int = 2) -> Tuple[np.ndarray, np.ndarray, Any]:
    """Run PCA on network metrics."""
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    X = metrics_df[metric_cols].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(X_scaled)
    
    logger.log("run_pca", n_components=n_components, explained_variance=float(pca.explained_variance_ratio_.sum()))
    
    return scores, pca.components_, pca


def compute_and_save_pca(metrics_df: pd.DataFrame, output_dir: str = "data/analysis") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute PCA and save loadings and scores."""
    os.makedirs(output_dir, exist_ok=True)
    
    scores, components, pca_obj = run_pca(metrics_df, n_components=2)
    
    loadings_df = pd.DataFrame(
        components.T,
        columns=['component_1', 'component_2'],
        index=['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    )
    loadings_path = os.path.join(output_dir, 'pca_loadings.csv')
    loadings_df.to_csv(loadings_path)
    logger.log("compute_and_save_pca", loadings_path=loadings_path)
    
    scores_df = pd.DataFrame(
        scores,
        columns=['pca_factor_1', 'pca_factor_2']
    )
    if 'subject_id' in metrics_df.columns:
        scores_df.insert(0, 'subject_id', metrics_df['subject_id'].values)
    
    scores_path = os.path.join(output_dir, 'factor_scores.csv')
    scores_df.to_csv(scores_path, index=False)
    logger.log("compute_and_save_pca", scores_path=scores_path)
    
    return loadings_df, scores_df


def merge_metrics_and_pca(metrics_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    """Merge raw metrics with PCA factor scores."""
    if 'subject_id' in metrics_df.columns and 'subject_id' in scores_df.columns:
        merged = pd.merge(metrics_df, scores_df, on='subject_id', how='inner')
    else:
        merged = pd.concat([metrics_df.reset_index(drop=True), scores_df.reset_index(drop=True)], axis=1)
    
    logger.log("merge_metrics_and_pca", merged_rows=len(merged), merged_cols=len(merged.columns))
    return merged


def apply_fdr_correction(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """Apply Benjamini-Hochberg FDR correction."""
    from statsmodels.stats.multitest import multipletests
    
    reject, q_values, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    logger.log("apply_fdr_correction", total_tests=len(p_values), significant=int(reject.sum()), alpha=alpha)
    return reject, q_values


def partial_correlation(x: np.ndarray, y: np.ndarray, covariates: np.ndarray) -> Tuple[float, float]:
    """Compute partial correlation controlling for covariates."""
    from scipy.stats import linregress
    
    residuals_x = x - np.polyfit(covariates, x, 1)[0] * covariates - np.polyfit(covariates, x, 1)[1]
    residuals_y = y - np.polyfit(covariates, y, 1)[0] * covariates - np.polyfit(covariates, y, 1)[1]
    
    r, p = stats.spearmanr(residuals_x, residuals_y)
    return r, p


def log_threshold_correlations(results_df: pd.DataFrame, threshold: float = 0.3) -> None:
    """Log correlations exceeding threshold."""
    significant = results_df[results_df['r'].abs() >= threshold]
    logger.log("log_threshold_correlations", threshold=threshold, count=len(significant))
    for idx, row in significant.iterrows():
        logger.log("significant_correlation", metric=row['metric'], r=float(row['r']), p=float(row['p']))


def calculate_batch_size_for_matrix_computation(
    n_metrics: int,
    n_subjects: int,
    dtype_bytes: int = 8,
    memory_limit_gb: float = 7.0
) -> int:
    """
    Calculate optimal batch size for matrix computations.
    
    For a correlation matrix of shape (n_metrics, n_subjects):
    - Each element is dtype_bytes (typically 8 for float64)
    - A batch processes batch_size subjects at a time
    - Memory per batch ≈ n_metrics * batch_size * dtype_bytes
    
    Args:
        n_metrics: Number of metrics (typically 4-6)
        n_subjects: Total number of subjects
        dtype_bytes: Bytes per element (default 8 for float64)
        memory_limit_gb: Memory limit in GB (default 7.0)
    
    Returns:
        Batch size (subjects per batch)
    """
    if n_metrics <= 0 or n_subjects <= 0:
        logger.log("calculate_batch_size_for_matrix_computation", warning="Invalid input dimensions")
        return max(1, n_subjects)
    
    memory_limit_bytes = memory_limit_gb * 1024 * 1024 * 1024
    bytes_per_subject = n_metrics * dtype_bytes
    
    batch_size = max(1, int(memory_limit_bytes / bytes_per_subject))
    batch_size = min(batch_size, n_subjects)
    
    logger.log(
        "calculate_batch_size_for_matrix_computation",
        n_metrics=n_metrics,
        n_subjects=n_subjects,
        memory_limit_gb=memory_limit_gb,
        batch_size=batch_size
    )
    
    return batch_size


def process_metrics_in_batches(
    metrics_df: pd.DataFrame,
    motor_scores: np.ndarray,
    fd_values: np.ndarray,
    metric_cols: Optional[List[str]] = None,
    batch_size: Optional[int] = None
) -> pd.DataFrame:
    """
    Process metrics in batches to respect memory constraints.
    
    Args:
        metrics_df: DataFrame with metric columns
        motor_scores: Motor performance scores
        fd_values: Framewise displacement values
        metric_cols: List of metric column names to process
        batch_size: Batch size (if None, calculated automatically)
    
    Returns:
        DataFrame with correlation results
    """
    if metric_cols is None:
        metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    metric_cols = [col for col in metric_cols if col in metrics_df.columns]
    
    if batch_size is None:
        batch_size = calculate_batch_size_for_matrix_computation(
            n_metrics=len(metric_cols),
            n_subjects=len(metrics_df)
        )
    
    logger.log("process_metrics_in_batches", total_metrics=len(metric_cols), batch_size=batch_size)
    
    results = []
    n_batches = (len(metric_cols) + batch_size - 1) // batch_size
    
    for batch_idx in range(n_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(metric_cols))
        batch_metrics = metric_cols[start_idx:end_idx]
        
        for metric in batch_metrics:
            metric_values = metrics_df[metric].values
            
            r, p = stats.spearmanr(metric_values, motor_scores)
            
            reject, q_values = apply_fdr_correction(np.array([p]))
            q = q_values[0]
            
            results.append({
                'metric': metric,
                'r': r,
                'p': p,
                'q': q,
                'significant': bool(reject[0])
            })
    
    results_df = pd.DataFrame(results)
    logger.log("process_metrics_in_batches", completed_metrics=len(results))
    
    return results_df


def run_metric_correlations(
    metrics_df: pd.DataFrame,
    motor_scores: np.ndarray,
    fd_values: np.ndarray
) -> pd.DataFrame:
    """
    Run correlations between metrics and motor performance.
    
    Args:
        metrics_df: DataFrame with metric columns
        motor_scores: Motor performance scores
        fd_values: Framewise displacement values
    
    Returns:
        DataFrame with correlation results
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    metric_cols = [col for col in metric_cols if col in metrics_df.columns]
    
    batch_size = calculate_batch_size_for_matrix_computation(
        n_metrics=len(metric_cols),
        n_subjects=len(metrics_df)
    )
    
    results_df = process_metrics_in_batches(
        metrics_df,
        motor_scores,
        fd_values,
        metric_cols=metric_cols,
        batch_size=batch_size
    )
    
    return results_df


def create_full_metrics_output(
    metrics_df: pd.DataFrame,
    pca_scores_df: pd.DataFrame,
    output_path: str = "data/analysis/full_metrics.csv"
) -> pd.DataFrame:
    """
    Create and save the full metrics output with all raw metrics and PCA factors.
    
    Args:
        metrics_df: DataFrame with raw metrics
        pca_scores_df: DataFrame with PCA factor scores
        output_path: Path to save the output CSV
    
    Returns:
        Merged DataFrame
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    merged = merge_metrics_and_pca(metrics_df, pca_scores_df)
    merged.to_csv(output_path, index=False)
    
    logger.log("create_full_metrics_output", output_path=output_path, rows=len(merged), cols=len(merged.columns))
    
    return merged


def main():
    """Main entry point for correlation analysis."""
    metrics_path = "data/processed/aggregated_metrics.csv"
    output_dir = "data/analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(metrics_path):
        logger.log("main", error=f"Metrics file not found: {metrics_path}")
        return
    
    metrics_df = load_metrics_data(metrics_path)
    
    loadings_df, scores_df = compute_and_save_pca(metrics_df, output_dir)
    
    full_metrics_df = create_full_metrics_output(metrics_df, scores_df, os.path.join(output_dir, 'full_metrics.csv'))
    
    if 'motor_score' in metrics_df.columns and 'fd' in metrics_df.columns:
        motor_scores = metrics_df['motor_score'].values
        fd_values = metrics_df['fd'].values
        
        results_df = run_metric_correlations(metrics_df, motor_scores, fd_values)
        
        results_path = os.path.join(output_dir, 'correlation_results.csv')
        results_df.to_csv(results_path, index=False)
        logger.log("main", results_path=results_path)
        
        log_threshold_correlations(results_df, threshold=0.3)
    
    logger.log("main", status="completed")


if __name__ == "__main__":
    main()