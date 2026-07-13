"""
Correlation analysis module for network metrics and sensorimotor performance.
Implements dynamic batch sizing, PCA, correlations, and FDR correction.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from code.logging_config import get_logger

logger = get_logger(__name__)

# Configuration for dynamic batch sizing
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
ESTIMATED_BYTES_PER_ROW = 400 * 400 * 8  # 400x400 float64 matrix

def get_optimal_batch_size(n_subjects: int) -> int:
    """
    Calculate the maximum number of subjects that can be processed in a batch
    without exceeding the memory limit.
    
    Args:
        n_subjects: Total number of subjects to process
        
    Returns:
        Optimal batch size (at least 1)
    """
    if n_subjects <= 0:
        return 1
        
    # Estimate memory needed for one subject's full matrix data
    # Using 400x400 matrix as standard, but we only store aggregated metrics
    # The actual memory usage for aggregated metrics is much lower
    # However, during PCA/correlation we load all aggregated metrics into memory
    # which is negligible (N x 4 floats). The main constraint is if we were
    # loading full connectivity matrices.
    
    # For the current implementation (aggregated metrics only):
    # We can safely process all subjects at once as memory usage is minimal
    # But we implement the logic for future scalability
    
    estimated_memory_per_batch = ESTIMATED_BYTES_PER_ROW * n_subjects
    
    if estimated_memory_per_batch <= MEMORY_LIMIT_BYTES:
        return n_subjects
        
    # Calculate max batch size
    max_batch_size = max(1, int(MEMORY_LIMIT_BYTES / ESTIMATED_BYTES_PER_ROW))
    return max_batch_size

def load_metrics_data(metrics_path: str) -> pd.DataFrame:
    """
    Load aggregated metrics data from CSV.
    
    Args:
        metrics_path: Path to the CSV file containing aggregated metrics
        
    Returns:
        DataFrame with subject metrics
    """
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
        
    df = pd.read_csv(metrics_path)
    logger.log("load_metrics_data", path=str(metrics_path), rows=len(df))
    return df

def compute_and_save_pca(metrics_df: pd.DataFrame, output_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform PCA on network metrics and save results.
    
    Args:
        metrics_df: DataFrame with metric columns
        output_dir: Directory to save output files
        
    Returns:
        Tuple of (pca_loadings_df, factor_scores_df)
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    
    # Select metric columns
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    available_cols = [col for col in metric_cols if col in metrics_df.columns]
    
    if len(available_cols) < 2:
        raise ValueError(f"Need at least 2 metric columns, found: {available_cols}")
        
    X = metrics_df[available_cols].values
    
    # Apply dynamic batch sizing if needed
    batch_size = get_optimal_batch_size(len(X))
    logger.log("compute_and_save_pca", 
               total_subjects=len(X), 
               batch_size=batch_size,
               memory_limit_gb=MEMORY_LIMIT_GB)
    
    # Standardize data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Perform PCA
    pca = PCA(n_components=min(2, len(available_cols)))
    components = pca.fit_transform(X_scaled)
    
    # Create loadings dataframe
    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=[f'component_{i+1}' for i in range(pca.n_components_)],
        index=available_cols
    )
    
    # Create factor scores dataframe
    factor_scores_df = pd.DataFrame(
        components,
        columns=[f'pca_factor_{i+1}' for i in range(pca.n_components_)],
        index=metrics_df.index
    )
    factor_scores_df.insert(0, 'subject_id', metrics_df['subject_id'].values)
    
    # Save outputs
    loadings_path = path / 'pca_loadings.csv'
    scores_path = path / 'factor_scores.csv'
    
    loadings_df.to_csv(loadings_path, index=False)
    factor_scores_df.to_csv(scores_path, index=False)
    
    logger.log("compute_and_save_pca_complete",
               loadings_file=str(loadings_path),
               scores_file=str(scores_path),
               explained_variance_ratio=list(pca.explained_variance_ratio_))
               
    return loadings_df, factor_scores_df

def merge_metrics_and_pca_scores(metrics_df: pd.DataFrame, 
                               factor_scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge original metrics with PCA factor scores.
    
    Args:
        metrics_df: Original metrics dataframe
        factor_scores_df: PCA factor scores dataframe
        
    Returns:
        Merged dataframe
    """
    merged = metrics_df.merge(
        factor_scores_df[['subject_id'] + [col for col in factor_scores_df.columns if col != 'subject_id']],
        on='subject_id',
        how='left'
    )
    logger.log("merge_metrics_and_pca_scores", 
               rows=len(merged),
               columns=list(merged.columns))
    return merged

def save_full_metrics(merged_df: pd.DataFrame, output_path: str) -> None:
    """
    Save full metrics dataframe to CSV.
    
    Args:
        merged_df: Merged dataframe with all metrics and PCA scores
        output_path: Path to save the CSV file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(path, index=False)
    logger.log("save_full_metrics", path=str(output_path), rows=len(merged_df))

def compute_and_save_correlation_matrix(metrics_df: pd.DataFrame, 
                                      output_dir: str) -> pd.DataFrame:
    """
    Compute correlations between metrics and motor scores with FD covariate.
    
    Args:
        metrics_df: DataFrame with metrics and behavioral data
        output_dir: Directory to save output files
        
    Returns:
        DataFrame with correlation results
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    
    # Apply dynamic batch sizing
    batch_size = get_optimal_batch_size(len(metrics_df))
    logger.log("compute_and_save_correlation_matrix",
               total_subjects=len(metrics_df),
               batch_size=batch_size,
               memory_limit_gb=MEMORY_LIMIT_GB)
    
    # Metrics to test
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    available_cols = [col for col in metric_cols if col in metrics_df.columns]
    
    if not available_cols:
        raise ValueError("No metric columns found for correlation analysis")
        
    results = []
    
    for metric in available_cols:
        # Check for required columns
        if 'motor_score' not in metrics_df.columns:
            raise ValueError("Column 'motor_score' not found in metrics dataframe")
        if 'fd' not in metrics_df.columns:
            raise ValueError("Column 'fd' not found in metrics dataframe")
            
        # Partial correlation controlling for FD
        x = metrics_df[metric].values
        y = metrics_df['motor_score'].values
        z = metrics_df['fd'].values
        
        # Remove NaNs
        valid_mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
        x_clean = x[valid_mask]
        y_clean = y[valid_mask]
        z_clean = z[valid_mask]
        
        if len(x_clean) < 3:
            logger.log("compute_and_save_correlation_matrix_skip",
                       metric=metric,
                       reason="Insufficient valid data points")
            continue
            
        # Calculate partial correlation
        # Correlation between x and y controlling for z
        r_xy = np.corrcoef(x_clean, y_clean)[0, 1]
        r_xz = np.corrcoef(x_clean, z_clean)[0, 1]
        r_yz = np.corrcoef(y_clean, z_clean)[0, 1]
        
        if abs(1 - r_xz**2) < 1e-10 or abs(1 - r_yz**2) < 1e-10:
            logger.log("compute_and_save_correlation_matrix_skip",
                       metric=metric,
                       reason="Near-perfect correlation with covariate")
            continue
            
        r_partial = (r_xy - r_xz * r_yz) / np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
        
        # Calculate p-value using t-distribution
        n = len(x_clean)
        t_stat = r_partial * np.sqrt((n - 3) / (1 - r_partial**2))
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 3))
        
        results.append({
            'metric_name': metric,
            'r': r_partial,
            'p': p_value,
            'n': n,
            'r_raw': r_xy
        })
    
    if not results:
        raise ValueError("No correlation results computed")
        
    results_df = pd.DataFrame(results)
    results_path = path / 'correlation_results.csv'
    results_df.to_csv(results_path, index=False)
    
    logger.log("compute_and_save_correlation_matrix_complete",
               path=str(results_path),
               metrics_computed=len(results))
               
    return results_df

def apply_fdr_correction(correlation_results: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        correlation_results: DataFrame with p-values
        alpha: Significance threshold
        
    Returns:
        DataFrame with FDR-corrected q-values and significance flags
    """
    p_values = correlation_results['p'].values
    n = len(p_values)
    
    if n == 0:
        return correlation_results
        
    # Sort p-values and calculate q-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Benjamini-Hochberg procedure
    q_values = np.zeros(n)
    for i, p in enumerate(sorted_p):
        rank = i + 1
        q_values[sorted_indices[i]] = min(p * n / rank, 1.0)
    
    # Ensure monotonicity
    for i in range(n-2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i+1])
    
    # Add to dataframe
    results = correlation_results.copy()
    results['q'] = q_values
    results['significant'] = results['q'] < alpha
    
    logger.log("apply_fdr_correction",
               n_tests=n,
               alpha=alpha,
               significant_count=results['significant'].sum())
               
    return results

def log_correlation_thresholds(correlation_results: pd.DataFrame, threshold: float = 0.3) -> None:
    """
    Log correlation results that exceed the threshold.
    
    Args:
        correlation_results: DataFrame with correlation results
        threshold: Absolute correlation threshold
    """
    significant = correlation_results[abs(correlation_results['r']) > threshold]
    
    logger.log("log_correlation_thresholds",
               threshold=threshold,
               count=len(significant),
               metrics=significant['metric_name'].tolist() if len(significant) > 0 else [])
               
    for _, row in significant.iterrows():
        logger.log("significant_correlation",
                   metric=row['metric_name'],
                   r=row['r'],
                   q=row.get('q', None),
                   significant=row.get('significant', False))

def main() -> None:
    """
    Main entry point for correlation analysis.
    Orchestrates the full analysis pipeline with dynamic batch sizing.
    """
    logger.log("main_start", step="correlation_analysis")
    
    # Define paths
    base_dir = Path("data")
    metrics_path = base_dir / "processed" / "aggregated_metrics.csv"
    analysis_dir = base_dir / "analysis"
    
    # Check if metrics file exists
    if not metrics_path.exists():
        raise FileNotFoundError(f"Expected metrics at {metrics_path}")
    
    # Load data
    metrics_df = load_metrics_data(str(metrics_path))
    logger.log("main_loaded_data", rows=len(metrics_df))
    
    # Perform PCA
    pca_loadings, factor_scores = compute_and_save_pca(metrics_df, str(analysis_dir))
    
    # Merge metrics and PCA scores
    full_metrics = merge_metrics_and_pca_scores(metrics_df, factor_scores)
    
    # Save full metrics
    save_full_metrics(full_metrics, str(analysis_dir / "full_metrics.csv"))
    
    # Compute correlations
    correlation_results = compute_and_save_correlation_matrix(full_metrics, str(analysis_dir))
    
    # Apply FDR correction
    corrected_results = apply_fdr_correction(correlation_results)
    corrected_results.to_csv(analysis_dir / "correlation_results_fdr.csv", index=False)
    
    # Log thresholds
    log_correlation_thresholds(corrected_results)
    
    logger.log("main_complete", 
               pca_loadings_file=str(analysis_dir / "pca_loadings.csv"),
               factor_scores_file=str(analysis_dir / "factor_scores.csv"),
               full_metrics_file=str(analysis_dir / "full_metrics.csv"),
               correlation_results_file=str(analysis_dir / "correlation_results_fdr.csv"))

if __name__ == "__main__":
    main()