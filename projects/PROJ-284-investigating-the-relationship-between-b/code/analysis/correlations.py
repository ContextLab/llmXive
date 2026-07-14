"""
Correlation analysis module.
Implements T024, T025, and related functionality.

Performs correlation analysis with FD covariate, FDR correction, and PCA.
"""
from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

from code.logging_config import get_logger

logger = get_logger(__name__)

def load_metrics_data(filepath: str) -> pd.DataFrame:
    """Load aggregated metrics data."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    return pd.read_csv(filepath)

def calculate_correlation_batch_size(available_memory_gb: float = 7.0) -> int:
    """Calculate optimal batch size for correlation computation."""
    # Rough estimate: 1000 subjects require ~100MB
    # Batch size = (available_memory * 1024) / 0.1
    return int((available_memory_gb * 1024) / 100)

def process_metrics_batch(df: pd.DataFrame, batch_size: int) -> List[pd.DataFrame]:
    """Split metrics dataframe into batches."""
    return [df[i:i+batch_size] for i in range(0, len(df), batch_size)]

def perform_pca_on_metrics(
    metrics_df: pd.DataFrame, 
    metric_columns: List[str] = None,
    n_components: int = 2
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform PCA on network metrics.
    
    Args:
        metrics_df: DataFrame with subject metrics
        metric_columns: Columns to include in PCA (default: modularity, global_efficiency, participation_coef, within_module_degree)
        n_components: Number of PCA components
        
    Returns:
        Tuple of (loadings_df, scores_df)
    """
    if metric_columns is None:
        metric_columns = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    # Filter available columns
    available_cols = [c for c in metric_columns if c in metrics_df.columns]
    if len(available_cols) < 2:
        logger.log("perform_pca_on_metrics", warning="Insufficient columns for PCA")
        # Return empty/placeholder
        return pd.DataFrame(), pd.DataFrame()
    
    # Handle missing values
    data = metrics_df[available_cols].dropna()
    if data.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Fit PCA
    pca = PCA(n_components=min(n_components, len(available_cols)))
    scores = pca.fit_transform(data)
    
    # Create loadings DataFrame
    loadings = pd.DataFrame(
        pca.components_.T,
        columns=[f'component_{i+1}' for i in range(pca.n_components_)],
        index=available_cols
    )
    
    # Create scores DataFrame with subject IDs
    scores_df = pd.DataFrame(
        scores,
        columns=[f'pca_factor_{i+1}' for i in range(pca.n_components_)],
        index=data.index
    )
    
    # Merge with original subject IDs if available
    if 'subject_id' in metrics_df.columns:
        scores_df = scores_df.reset_index(drop=True)
        scores_df['subject_id'] = metrics_df.loc[data.index, 'subject_id'].values
    
    return loadings, scores_df

def save_pca_results(loadings: pd.DataFrame, scores: pd.DataFrame, output_dir: str) -> None:
    """Save PCA results to CSV files."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    loadings_path = Path(output_dir) / "pca_loadings.csv"
    scores_path = Path(output_dir) / "factor_scores.csv"
    
    loadings.to_csv(loadings_path, index=True)
    scores.to_csv(scores_path, index=False)
    
    logger.log("save_pca_results", status="success", loadings_path=str(loadings_path), scores_path=str(scores_path))

def generate_full_metrics(
    metrics_df: pd.DataFrame, 
    pca_scores: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge individual metrics with PCA factor scores.
    
    Ensures FR-005 (FDR on individual metrics) and FR-004 (report generation) 
    have access to all data.
    """
    if pca_scores.empty:
        return metrics_df
    
    # Merge on index or subject_id
    if 'subject_id' in pca_scores.columns and 'subject_id' in metrics_df.columns:
        merged = pd.merge(metrics_df, pca_scores, on='subject_id', how='left')
    else:
        # Fallback to index
        merged = pd.concat([metrics_df, pca_scores], axis=1)
    
    return merged

def save_full_metrics(df: pd.DataFrame, output_path: str) -> None:
    """Save full metrics DataFrame to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.log("save_full_metrics", status="success", path=output_path, rows=len(df))

def run_correlations_with_fd_covariate(
    metrics_df: pd.DataFrame,
    target_column: str = 'motor_score',
    fd_column: str = 'fd'
) -> pd.DataFrame:
    """
    Perform Spearman/Pearson correlation with FD as covariate.
    
    Applies to individual metrics for FDR correction as required by FR-005.
    
    Args:
        metrics_df: DataFrame with metrics and behavioral data
        target_column: Behavioral target variable
        fd_column: Framewise Displacement column
        
    Returns:
        DataFrame with correlation results (metric_name, r, p, q, significant)
    """
    results = []
    
    # Get metric columns (exclude metadata)
    metric_cols = [
        'modularity', 'global_efficiency', 'participation_coef', 'within_module_degree'
    ]
    available_metrics = [c for c in metric_cols if c in metrics_df.columns]
    
    if target_column not in metrics_df.columns:
        logger.log("run_correlations_with_fd_covariate", error=f"Target column {target_column} not found")
        return pd.DataFrame(columns=['metric_name', 'r', 'p', 'q', 'significant'])
    
    for metric in available_metrics:
        # Drop rows with NaN in either variable
        valid_data = metrics_df[[metric, target_column, fd_column]].dropna()
        if len(valid_data) < 5:
            results.append({
                'metric_name': metric,
                'r': np.nan,
                'p': np.nan,
                'q': np.nan,
                'significant': False,
                'n': len(valid_data)
            })
            continue
        
        # Partial correlation controlling for FD
        # Using scipy's partial correlation approach via residuals
        x = valid_data[metric].values
        y = valid_data[target_column].values
        z = valid_data[fd_column].values
        
        # Regress out FD from both X and Y
        res_x = stats.linregress(z, x).resid
        res_y = stats.linregress(z, y).resid
        
        # Correlate residuals
        r, p = stats.spearmanr(res_x, res_y)
        
        results.append({
            'metric_name': metric,
            'r': r,
            'p': p,
            'q': np.nan,  # Will be filled after FDR
            'significant': False,  # Will be updated after FDR
            'n': len(valid_data)
        })
    
    return pd.DataFrame(results)

def apply_fdr_correction(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        results_df: DataFrame with 'p' column
        alpha: FDR threshold
        
    Returns:
        Updated DataFrame with 'q' and 'significant' columns
    """
    if results_df.empty:
        return results_df
    
    p_values = results_df['p'].dropna().values
    if len(p_values) == 0:
        return results_df
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    n = len(sorted_p)
    
    # Calculate q-values
    q_values = np.zeros(n)
    for i, p in enumerate(sorted_p):
        q_values[i] = p * n / (i + 1)
    
    # Ensure monotonicity (from largest to smallest)
    for i in range(n-2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i+1])
    
    # Map back to original order
    q_map = np.zeros(n)
    q_map[sorted_indices] = q_values
    
    # Update DataFrame
    results_df = results_df.copy()
    results_df['q'] = q_map
    results_df['significant'] = results_df['q'] < alpha
    
    return results_df

def save_correlation_results(df: pd.DataFrame, output_path: str) -> None:
    """Save correlation results to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.log("save_correlation_results", status="success", path=output_path, rows=len(df))

def log_significant_correlations(df: pd.DataFrame, threshold_r: float = 0.3) -> None:
    """Log significant correlations above threshold."""
    significant = df[(df['significant']) & (df['r'].abs() > threshold_r)]
    for _, row in significant.iterrows():
        logger.log(
            "significant_correlation",
            metric=row['metric_name'],
            r=row['r'],
            q=row['q'],
            threshold=threshold_r
        )

def main() -> None:
    """Main entry point for correlation analysis."""
    # Paths
    metrics_path = Path("data/processed/aggregated_metrics.csv")
    corr_output = Path("data/analysis/correlations.csv")
    pca_loadings_path = Path("data/analysis/pca_loadings.csv")
    factor_scores_path = Path("data/analysis/factor_scores.csv")
    full_metrics_path = Path("data/analysis/full_metrics.csv")
    
    # Load metrics
    if not metrics_path.exists():
        logger.log("correlation_main", error=f"Metrics file not found: {metrics_path}")
        print(f"Error: Metrics file not found at {metrics_path}")
        return
    
    try:
        metrics_df = load_metrics_data(str(metrics_path))
    except Exception as e:
        logger.log("correlation_main", error=f"Failed to load metrics: {e}")
        print(f"Error loading metrics: {e}")
        return
    
    # Run correlations
    logger.log("correlation_main", status="info", message="Running correlations with FD covariate")
    corr_results = run_correlations_with_fd_covariate(metrics_df)
    
    # Apply FDR
    corr_results = apply_fdr_correction(corr_results)
    
    # Log significant results
    log_significant_correlations(corr_results)
    
    # Save correlation results
    save_correlation_results(corr_results, str(corr_output))
    print(f"Correlation results saved to {corr_output}")
    
    # Perform PCA
    logger.log("correlation_main", status="info", message="Performing PCA on metrics")
    if 'subject_id' in metrics_df.columns:
        loadings, scores = perform_pca_on_metrics(metrics_df)
    else:
        # Add dummy index
        metrics_df_temp = metrics_df.copy()
        metrics_df_temp['subject_id'] = range(len(metrics_df_temp))
        loadings, scores = perform_pca_on_metrics(metrics_df_temp)
    
    # Save PCA results
    if not loadings.empty:
        save_pca_results(loadings, scores, str(Path("data/analysis")))
        print(f"PCA loadings saved to {pca_loadings_path}")
        print(f"Factor scores saved to {factor_scores_path}")
    
    # Generate and save full metrics
    if not scores.empty:
        full_df = generate_full_metrics(metrics_df, scores)
        save_full_metrics(full_df, str(full_metrics_path))
        print(f"Full metrics saved to {full_metrics_path}")
    else:
        save_full_metrics(metrics_df, str(full_metrics_path))
        print(f"Full metrics (without PCA) saved to {full_metrics_path}")

if __name__ == "__main__":
    main()
