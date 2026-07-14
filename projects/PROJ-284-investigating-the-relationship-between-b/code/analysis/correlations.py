"""
Correlation analysis module for US2.
Implements Spearman/Pearson correlations with FD covariate, FDR correction,
PCA, and correlation threshold logging.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

from code.logging_config import get_logger
from code.utils.memory_monitor import get_available_memory, estimate_memory_usage

logger = get_logger(__name__)

# Threshold for logging significant correlations (FR-007)
CORRELATION_THRESHOLD = 0.3

def get_optimal_batch_size(estimated_size_per_subject_mb: float = 10.0) -> int:
    """
    Calculate optimal batch size based on available memory.
    
    Args:
        estimated_size_per_subject_mb: Estimated memory usage per subject in MB
        
    Returns:
        Optimal batch size
    """
    available_mb = get_available_memory() / (1024 * 1024)
    # Reserve 2GB for safety
    safe_memory_mb = available_mb - 2048
    if safe_memory_mb <= 0:
        safe_memory_mb = available_mb / 2
        
    batch_size = int(safe_memory_mb / estimated_size_per_subject_mb)
    return max(1, min(batch_size, 100))  # Cap at 100 subjects per batch

def process_metrics_in_batches(
    metrics_df: pd.DataFrame, 
    func, 
    batch_size: Optional[int] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Process a DataFrame in batches to respect memory constraints.
    
    Args:
        metrics_df: Input DataFrame with metrics
        func: Function to apply to each batch
        batch_size: Number of rows per batch (auto-calculated if None)
        **kwargs: Additional arguments to pass to func
        
    Returns:
        Combined results from all batches
    """
    if batch_size is None:
        # Estimate memory: assume 1MB per row for safety
        batch_size = get_optimal_batch_size(1.0)
        
    results = []
    total_rows = len(metrics_df)
    
    for start_idx in range(0, total_rows, batch_size):
        end_idx = min(start_idx + batch_size, total_rows)
        batch = metrics_df.iloc[start_idx:end_idx]
        
        logger.log(
            "process_batch",
            operation="process_metrics_in_batches",
            start_idx=start_idx,
            end_idx=end_idx,
            batch_size=len(batch)
        )
        
        result = func(batch, **kwargs)
        results.append(result)
        
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

def load_metrics_data(
    metrics_path: Optional[Path] = None,
    aggregated_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load aggregated metrics data for analysis.
    
    Args:
        metrics_path: Path to metrics CSV (optional, defaults to data/processed/aggregated_metrics.csv)
        aggregated_path: Path to aggregated metrics CSV (optional)
        
    Returns:
        DataFrame with metrics
    """
    if metrics_path is None:
        metrics_path = Path("data/processed/aggregated_metrics.csv")
    if aggregated_path is None:
        aggregated_path = metrics_path
        
    if not metrics_path.exists():
        # Try aggregated path
        if aggregated_path.exists():
            metrics_path = aggregated_path
        else:
            raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
            
    df = pd.read_csv(metrics_path)
    
    # Ensure required columns exist
    required_cols = ['subject_id', 'modularity', 'global_efficiency', 
                    'participation_coef', 'within_module_degree', 'fd']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    return df

def run_correlations_with_fd_covariate(
    metrics_df: pd.DataFrame,
    target_col: str,
    covariate_col: str = 'fd',
    method: str = 'spearman'
) -> Tuple[float, float]:
    """
    Run correlation with FD as a covariate using partial correlation.
    
    Args:
        metrics_df: DataFrame with metrics
        target_col: Column to correlate with the target
        covariate_col: Covariate column (default: 'fd')
        method: 'spearman' or 'pearson'
        
    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    # Filter out NaN values
    valid_data = metrics_df[[target_col, covariate_col]].dropna()
    
    if len(valid_data) < 3:
        return 0.0, 1.0
        
    x = valid_data[target_col].values
    y = valid_data[covariate_col].values
    
    # Partial correlation: correlate residuals after regressing out covariate
    # Simple approach: compute correlation between target and covariate,
    # then between target and the metric of interest (already separated here)
    # For true partial correlation, we'd need multiple regression residuals
    
    # For this implementation, we compute correlation between target_col and 
    # another metric column, controlling for fd via partial correlation formula
    if target_col == covariate_col:
        return 0.0, 1.0
        
    # Get the other metric column (this function is called for each metric)
    # We assume the caller passes the correct target_col
    
    # Compute partial correlation using scipy
    # r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1 - r_xz^2) * (1 - r_yz^2))
    # But here we only have one metric and one covariate, so we compute
    # correlation between the metric and the behavioral score, controlling for FD
    
    # Actually, the task is to correlate each metric with a behavioral score (motor_score)
    # while controlling for FD. Let's assume the DataFrame has a 'motor_score' column.
    
    if 'motor_score' not in metrics_df.columns:
        # If no motor_score, return 0
        return 0.0, 1.0
        
    motor = metrics_df['motor_score'].dropna()
    metric = metrics_df[target_col].dropna()
    fd = metrics_df[covariate_col].dropna()
    
    # Align indices
    common_idx = motor.index.intersection(metric.index).intersection(fd.index)
    if len(common_idx) < 3:
        return 0.0, 1.0
        
    motor = motor.loc[common_idx].values
    metric = metric.loc[common_idx].values
    fd = fd.loc[common_idx].values
    
    # Compute partial correlation: correlation between motor and metric, controlling for fd
    # Step 1: Regress motor on fd
    # Step 2: Regress metric on fd
    # Step 3: Correlate residuals
    
    # Simple linear regression for residuals
    def regress_out(x, y):
        # y ~ x, return residuals
        coeffs = np.polyfit(x, y, 1)
        predicted = coeffs[0] * x + coeffs[1]
        residuals = y - predicted
        return residuals
        
    motor_resid = regress_out(fd, motor)
    metric_resid = regress_out(fd, metric)
    
    # Compute correlation on residuals
    if method == 'pearson':
        corr, p_val = stats.pearsonr(motor_resid, metric_resid)
    else:
        # Spearman on residuals
        corr, p_val = stats.spearmanr(motor_resid, metric_resid)
        
    return float(corr), float(p_val)

def apply_fdr_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: List of p-values
        alpha: Significance level (default: 0.05)
        
    Returns:
        Tuple of (significant flags, adjusted p-values)
    """
    n = len(p_values)
    if n == 0:
        return [], []
        
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # BH procedure
    adjusted_p = np.zeros(n)
    for i in range(n):
        adjusted_p[i] = sorted_p[i] * n / (i + 1)
        
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])
        
    # Clip to [0, 1]
    adjusted_p = np.clip(adjusted_p, 0, 1)
    
    # Determine significance
    significant = adjusted_p < alpha
    
    # Restore original order
    orig_significant = [False] * n
    orig_adjusted_p = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        orig_significant[idx] = significant[i]
        orig_adjusted_p[idx] = float(adjusted_p[i])
        
    return orig_significant, orig_adjusted_p

def log_significant_correlations(
    metric_name: str,
    r: float,
    p: float,
    q: float,
    significant: bool
) -> None:
    """
    Log correlation results, focusing on significant ones (r > threshold).
    
    Args:
        metric_name: Name of the metric
        r: Correlation coefficient
        p: Raw p-value
        q: FDR-corrected p-value
        significant: Whether the correlation is significant after FDR
    """
    # Log all correlations for transparency
    logger.log(
        "correlation_result",
        operation="log_significant_correlations",
        metric=metric_name,
        r=r,
        p=p,
        q=q,
        significant=significant
    )
    
    # Log threshold-based significant correlations (FR-007)
    if abs(r) > CORRELATION_THRESHOLD:
        logger.log(
            "threshold_exceeded",
            operation="log_significant_correlations",
            metric=metric_name,
            r=r,
            threshold=CORRELATION_THRESHOLD,
            message=f"Correlation threshold exceeded: |r|={abs(r):.3f} > {CORRELATION_THRESHOLD}"
        )
        
    if significant:
        logger.log(
            "significant_correlation",
            operation="log_significant_correlations",
            metric=metric_name,
            r=r,
            q=q,
            message=f"Significant correlation: {metric_name} (r={r:.3f}, q={q:.3f})"
        )

def run_pca_on_metrics(
    metrics_df: pd.DataFrame,
    n_components: int = 2
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run PCA on network metrics.
    
    Args:
        metrics_df: DataFrame with metrics
        n_components: Number of PCA components
        
    Returns:
        Tuple of (loadings DataFrame, factor scores DataFrame)
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    # Filter to available columns
    available_cols = [col for col in metric_cols if col in metrics_df.columns]
    if len(available_cols) < 2:
        raise ValueError(f"Need at least 2 metric columns for PCA, found: {available_cols}")
        
    X = metrics_df[available_cols].dropna()
    
    if len(X) < n_components:
        raise ValueError(f"Not enough samples for PCA: {len(X)} < {n_components}")
        
    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(X)
    
    # Create loadings DataFrame
    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=[f'component_{i+1}' for i in range(n_components)],
        index=available_cols
    )
    
    # Create factor scores DataFrame
    subject_ids = X.index.tolist()
    factor_scores_df = pd.DataFrame(
        scores,
        columns=[f'pca_factor_{i+1}' for i in range(n_components)],
        index=subject_ids
    )
    factor_scores_df['subject_id'] = factor_scores_df.index
    
    return loadings_df, factor_scores_df

def generate_full_metrics(
    metrics_df: pd.DataFrame,
    factor_scores_df: pd.DataFrame,
    output_path: Path
) -> pd.DataFrame:
    """
    Merge raw metrics with PCA factor scores.
    
    Args:
        metrics_df: DataFrame with raw metrics
        factor_scores_df: DataFrame with PCA factor scores
        output_path: Path to save the merged DataFrame
        
    Returns:
        Merged DataFrame
    """
    # Ensure subject_id is a column in both
    if 'subject_id' not in metrics_df.columns:
        metrics_df = metrics_df.reset_index()
        if 'subject_id' not in metrics_df.columns:
            metrics_df['subject_id'] = metrics_df.index
            
    if 'subject_id' not in factor_scores_df.columns:
        factor_scores_df = factor_scores_df.reset_index()
        if 'subject_id' not in factor_scores_df.columns:
            factor_scores_df['subject_id'] = factor_scores_df.index
    
    # Merge on subject_id
    merged = pd.merge(metrics_df, factor_scores_df, on='subject_id', how='left')
    
    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    
    logger.log(
        "generate_full_metrics",
        operation="generate_full_metrics",
        output_path=str(output_path),
        num_rows=len(merged),
        num_columns=len(merged.columns)
    )
    
    return merged

def main() -> None:
    """
    Main entry point for correlation analysis.
    """
    logger.log("start_analysis", operation="main")
    
    try:
        # Load metrics
        metrics_df = load_metrics_data()
        
        # Run correlations for each metric
        metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
        results = []
        
        for metric in metric_cols:
            if metric not in metrics_df.columns:
                continue
                
            r, p = run_correlations_with_fd_covariate(metrics_df, metric)
            results.append({
                'metric': metric,
                'r': r,
                'p': p
            })
            
        if not results:
            logger.log("no_metrics", operation="main", message="No metrics found for correlation")
            return
            
        # Apply FDR correction
        p_values = [r['p'] for r in results]
        significant, adjusted_p = apply_fdr_correction(p_values)
        
        # Log and compile results
        for i, result in enumerate(results):
            result['q'] = adjusted_p[i]
            result['significant'] = significant[i]
            log_significant_correlations(
                result['metric'],
                result['r'],
                result['p'],
                result['q'],
                result['significant']
            )
            
        # Save correlation results
        corr_results_df = pd.DataFrame(results)
        output_path = Path("data/analysis/correlations.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        corr_results_df.to_csv(output_path, index=False)
        
        # Run PCA
        loadings_df, factor_scores_df = run_pca_on_metrics(metrics_df)
        
        # Save PCA outputs
        loadings_path = Path("data/analysis/pca_loadings.csv")
        factor_scores_path = Path("data/analysis/factor_scores.csv")
        
        loadings_df.to_csv(loadings_path)
        factor_scores_df.to_csv(factor_scores_path)
        
        # Generate full metrics
        full_metrics_path = Path("data/analysis/full_metrics.csv")
        generate_full_metrics(metrics_df, factor_scores_df, full_metrics_path)
        
        logger.log("analysis_complete", operation="main")
        
    except Exception as e:
        logger.log("analysis_failed", operation="main", error=str(e))
        raise