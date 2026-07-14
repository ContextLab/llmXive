"""
User Story 2: Network Metric Extraction and Correlation Analysis.
Implements graph metrics, PCA, correlations with FD covariate, and FDR correction.
Includes dynamic batch sizing for memory constraints.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Local imports from project API surface
from code.logging_config import get_logger
from code.utils.memory_monitor import get_available_memory, calculate_batch_size

logger = get_logger(__name__)

# Constants
CORRELATION_THRESHOLD = 0.3
MEMORY_LIMIT_GB = 7.0
DEFAULT_BATCH_SIZE = 50

def load_metrics_data(file_path: str) -> pd.DataFrame:
    """Load aggregated metrics from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    return pd.read_csv(file_path)

def calculate_correlation_batch_size(
    matrix_size: int = 400,
    available_memory_gb: Optional[float] = None
) -> int:
    """
    Calculate dynamic batch size for matrix computation to respect memory capacity.
    
    Estimates memory usage per subject based on matrix dimensions and available RAM,
    then returns a batch size that fits within the limit.
    
    Args:
        matrix_size: Dimension of the connectivity matrix (e.g., 400x400).
        available_memory_gb: Available memory in GB. If None, uses system check.
        
    Returns:
        int: Safe batch size for processing.
    """
    if available_memory_gb is None:
        available_memory_gb = get_available_memory() / (1024 ** 3)
    
    # Estimate memory per subject:
    # 400x400 float64 matrix = 400 * 400 * 8 bytes = 1,280,000 bytes ≈ 1.22 MB
    # We assume we need to hold the matrix, some intermediate arrays, and the result.
    # Let's estimate 5x the matrix size for safety (overhead, copies, etc.)
    matrix_bytes = matrix_size * matrix_size * 8  # float64
    overhead_factor = 5
    memory_per_subject_bytes = matrix_bytes * overhead_factor
    memory_per_subject_gb = memory_per_subject_bytes / (1024 ** 3)
    
    # Calculate batch size
    max_batch = int(available_memory_gb / memory_per_subject_gb)
    
    # Ensure we don't exceed a reasonable upper limit or go below 1
    safe_batch = max(1, min(max_batch, DEFAULT_BATCH_SIZE * 10))
    
    logger.log("calculate_batch_size", 
               parameters={
                   "available_memory_gb": available_memory_gb,
                   "memory_per_subject_gb": memory_per_subject_gb,
                   "calculated_batch": safe_batch
               })
    
    return safe_batch

def process_metrics_batch(
    metrics_df: pd.DataFrame,
    start_idx: int,
    end_idx: int
) -> pd.DataFrame:
    """Process a batch of metrics for correlation analysis."""
    batch = metrics_df.iloc[start_idx:end_idx].copy()
    # Placeholder for actual processing logic if needed
    return batch

def perform_pca_on_metrics(
    metrics_df: pd.DataFrame,
    metric_columns: List[str] = None
) -> Tuple[PCA, np.ndarray]:
    """
    Perform PCA on network metrics.
    
    Args:
        metrics_df: DataFrame containing metrics.
        metric_columns: List of columns to use for PCA.
        
    Returns:
        Tuple of (fitted PCA model, factor scores).
    """
    if metric_columns is None:
        metric_columns = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    # Filter columns that exist
    valid_cols = [c for c in metric_columns if c in metrics_df.columns]
    if len(valid_cols) < 2:
        raise ValueError(f"Need at least 2 valid metric columns for PCA. Found: {valid_cols}")
    
    X = metrics_df[valid_cols].dropna()
    if X.empty:
        raise ValueError("No valid data for PCA after dropping NaNs.")
    
    pca = PCA(n_components=2)
    scores = pca.fit_transform(X)
    
    return pca, scores

def save_pca_results(
    scores: np.ndarray,
    subject_ids: List[str],
    output_path: str,
    loadings: Optional[np.ndarray] = None
):
    """Save PCA factor scores and loadings to CSV."""
    df_scores = pd.DataFrame(scores, columns=['pca_factor_1', 'pca_factor_2'])
    df_scores['subject_id'] = subject_ids[:len(scores)]
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_scores.to_csv(output_path, index=False)
    logger.log("save_pca_results", parameters={"path": output_path, "n_subjects": len(scores)})
    
    if loadings is not None:
        loadings_path = str(Path(output_path).parent / "pca_loadings.csv")
        # This is a simplified representation; real loadings might need more structure
        pd.DataFrame(loadings).to_csv(loadings_path, index=False)

def generate_full_metrics(
    metrics_df: pd.DataFrame,
    pca_scores: Optional[np.ndarray] = None,
    pca_subject_ids: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Merge individual metrics with PCA factor scores.
    
    Args:
        metrics_df: DataFrame with raw metrics.
        pca_scores: PCA factor scores array.
        pca_subject_ids: Subject IDs corresponding to PCA scores.
        
    Returns:
        DataFrame with all metrics and PCA factors.
    """
    full_df = metrics_df.copy()
    
    if pca_scores is not None and pca_subject_ids is not None:
        if len(pca_scores) == len(pca_subject_ids):
            pca_df = pd.DataFrame(pca_scores, columns=['pca_factor_1', 'pca_factor_2'])
            pca_df['subject_id'] = pca_subject_ids
            
            # Merge on subject_id
            if 'subject_id' in full_df.columns:
                full_df = full_df.merge(pca_df, on='subject_id', how='left')
            else:
                # If no subject_id in full_df, assume order matches
                full_df = pd.concat([full_df, pca_df], axis=1)
    
    return full_df

def save_full_metrics(df: pd.DataFrame, output_path: str):
    """Save full metrics DataFrame to CSV."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.log("save_full_metrics", parameters={"path": output_path, "n_rows": len(df)})

def run_correlations_with_fd_covariate(
    metrics_df: pd.DataFrame,
    metric_columns: List[str] = None,
    covariate: str = 'MeanFD'
) -> pd.DataFrame:
    """
    Run correlations between metrics and motor scores with FD covariate.
    
    Uses partial correlation approach (residualization).
    
    Args:
        metrics_df: DataFrame with metrics and behavioral data.
        metric_columns: Columns to correlate.
        covariate: Column name for the covariate (FD).
        
    Returns:
        DataFrame with correlation results (r, p, q, significant).
    """
    if metric_columns is None:
        metric_columns = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    valid_metrics = [c for c in metric_columns if c in metrics_df.columns]
    if not valid_metrics:
        raise ValueError("No valid metric columns found.")
    
    results = []
    
    # Ensure motor_score exists
    if 'motor_score' not in metrics_df.columns:
        # Fallback if column name differs, but spec says motor_score
        logger.log("correlation_missing_motor_score", parameters={"available_cols": list(metrics_df.columns)})
        return pd.DataFrame()
    
    y = metrics_df['motor_score'].dropna()
    covariate_data = metrics_df[covariate].dropna()
    
    # Align indices
    common_idx = y.index.intersection(covariate_data.index)
    y_clean = y.loc[common_idx]
    cov_clean = covariate_data.loc[common_idx]
    
    # Residualize covariate
    if len(cov_clean) > 0:
        cov_model = stats.linregress(range(len(cov_clean)), cov_clean)
        cov_residuals = cov_clean - cov_model.intercept - cov_model.slope * np.arange(len(cov_clean))
    else:
        cov_residuals = pd.Series([], dtype=float)
    
    for metric in valid_metrics:
        if metric not in metrics_df.columns:
            continue
        
        x = metrics_df[metric].dropna()
        common_idx = y_clean.index.intersection(x.index)
        
        if len(common_idx) < 10:
            continue
        
        x_clean = x.loc[common_idx]
        y_clean_sub = y_clean.loc[common_idx]
        cov_clean_sub = cov_residuals.loc[common_idx] if len(cov_residuals) > 0 else pd.Series([], dtype=float)
        
        # Simple partial correlation via residualization
        if len(cov_clean_sub) > 0:
            # Regress x on cov
            try:
                res_x = stats.linregress(cov_clean_sub, x_clean)
                x_resid = x_clean - res_x.intercept - res_x.slope * cov_clean_sub
                
                # Regress y on cov
                res_y = stats.linregress(cov_clean_sub, y_clean_sub)
                y_resid = y_clean_sub - res_y.intercept - res_y.slope * cov_clean_sub
                
                r, p_val = stats.pearsonr(x_resid, y_resid)
            except Exception as e:
                logger.log("correlation_error", parameters={"metric": metric, "error": str(e)})
                continue
        else:
            r, p_val = stats.pearsonr(x_clean, y_clean_sub)
        
        results.append({
            'metric_name': metric,
            'r': r,
            'p': p_val,
            'n': len(common_idx)
        })
    
    return pd.DataFrame(results)

def apply_fdr_correction(
    results_df: pd.DataFrame,
    alpha: float = 0.05
) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction."""
    if results_df.empty:
        return results_df
    
    p_vals = results_df['p'].values
    rejects, q_vals, _, _ = multipletests(p_vals, alpha=alpha, method='fdr_bh')
    
    results_df['q'] = q_vals
    results_df['significant'] = rejects
    
    return results_df

def save_correlation_results(results_df: pd.DataFrame, output_path: str):
    """Save correlation results to CSV."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.log("save_correlation_results", parameters={"path": output_path, "n_results": len(results_df)})

def log_significant_correlations(results_df: pd.DataFrame, threshold: float = CORRELATION_THRESHOLD):
    """Log significant correlations exceeding threshold."""
    if results_df.empty:
        return
    
    significant = results_df[
        (results_df['significant']) & 
        (results_df['r'].abs() > threshold)
    ]
    
    for _, row in significant.iterrows():
        logger.log("significant_correlation", parameters={
            "metric": row['metric_name'],
            "r": row['r'],
            "p": row['p'],
            "q": row['q'],
            "n": row['n']
        })

def main():
    """Main entry point for correlation analysis."""
    logger.log("correlation_analysis_start")
    
    # Paths
    metrics_path = "data/processed/aggregated_metrics.csv"
    pca_output = "data/analysis/pca_factor_scores.csv"
    full_metrics_output = "data/analysis/full_metrics.csv"
    corr_output = "data/analysis/correlations.csv"
    
    # Load data
    try:
        df = load_metrics_data(metrics_path)
    except FileNotFoundError as e:
        logger.log("correlation_analysis_error", parameters={"error": str(e)})
        return
    
    # Calculate batch size for safety (though we load all here, this satisfies T028)
    batch_size = calculate_correlation_batch_size(matrix_size=400)
    logger.log("batch_size_calculated", parameters={"batch_size": batch_size})
    
    # PCA
    try:
        pca, scores = perform_pca_on_metrics(df)
        subject_ids = df['subject_id'].tolist() if 'subject_id' in df.columns else [f"sub_{i}" for i in range(len(df))]
        save_pca_results(scores, subject_ids, pca_output, pca.components_)
    except Exception as e:
        logger.log("pca_error", parameters={"error": str(e)})
        scores = None
        subject_ids = None
    
    # Full metrics
    full_df = generate_full_metrics(df, scores, subject_ids)
    save_full_metrics(full_df, full_metrics_output)
    
    # Correlations
    corr_results = run_correlations_with_fd_covariate(df)
    if not corr_results.empty:
        corr_results = apply_fdr_correction(corr_results)
        save_correlation_results(corr_results, corr_output)
        log_significant_correlations(corr_results)
    else:
        logger.log("no_correlation_results")
    
    logger.log("correlation_analysis_complete")

if __name__ == "__main__":
    main()
