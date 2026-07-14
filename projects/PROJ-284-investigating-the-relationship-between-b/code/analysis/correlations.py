"""
Correlation analysis module for network metrics.
Implements T024, T025, T027 and supports T023b.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from code.logging_config import get_logger

logger = get_logger(__name__)

def load_metrics_data(
    file_path: str = "data/processed/aggregated_metrics.csv"
) -> pd.DataFrame:
    """
    Load aggregated metrics data from CSV.
    
    Args:
        file_path: Path to the aggregated metrics CSV file
        
    Returns:
        DataFrame with metrics data
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    logger.log("metrics_data_loaded", path=file_path, rows=len(df))
    return df

def perform_pca_on_metrics(
    df: pd.DataFrame,
    metric_columns: List[str] = None
) -> Tuple[Any, pd.DataFrame]:
    """
    Perform PCA on network metrics.
    
    Args:
        df: DataFrame with metric columns
        metric_columns: List of columns to use for PCA
        
    Returns:
        PCA object and DataFrame with factor scores
    """
    from sklearn.decomposition import PCA
    
    if metric_columns is None:
        metric_columns = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    # Filter to available columns
    available_cols = [c for c in metric_columns if c in df.columns]
    if len(available_cols) < 2:
        raise ValueError(f"Need at least 2 metric columns for PCA, found: {available_cols}")
    
    pca_data = df[available_cols].dropna()
    pca = PCA(n_components=min(2, len(available_cols)))
    scores = pca.fit_transform(pca_data)
    
    # Create factor scores DataFrame
    factor_cols = [f'pca_factor_{i+1}' for i in range(scores.shape[1])]
    factor_df = pd.DataFrame(scores, columns=factor_cols, index=pca_data.index)
    factor_df['subject_id'] = df.loc[pca_data.index, 'subject_id'].values
    
    logger.log("pca_performed", n_components=len(factor_cols), n_samples=len(factor_df))
    return pca, factor_df

def save_pca_results(
    pca: Any,
    factor_df: pd.DataFrame,
    loadings_path: str = "data/analysis/pca_loadings.csv",
    scores_path: str = "data/analysis/factor_scores.csv"
):
    """
    Save PCA results to CSV files.
    
    Args:
        pca: Fitted PCA object
        factor_df: DataFrame with factor scores
        loadings_path: Path for loadings file
        scores_path: Path for scores file
    """
    # Create loadings DataFrame
    loadings = pd.DataFrame(
        pca.components_.T,
        columns=[f'component_{i+1}' for i in range(pca.n_components_)],
        index=pca.feature_names_in_
    )
    
    # Ensure directories exist
    Path(loadings_path).parent.mkdir(parents=True, exist_ok=True)
    Path(scores_path).parent.mkdir(parents=True, exist_ok=True)
    
    loadings.to_csv(loadings_path, index=True)
    factor_df.to_csv(scores_path, index=False)
    
    logger.log("pca_results_saved", loadings_path=loadings_path, scores_path=scores_path)

def generate_full_metrics(
    metrics_df: pd.DataFrame,
    factor_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge individual metric columns with PCA factor scores.
    
    Args:
        metrics_df: DataFrame with raw metrics
        factor_df: DataFrame with PCA factor scores
        
    Returns:
        Combined DataFrame with all metrics and factors
    """
    # Merge on subject_id
    merged = pd.merge(metrics_df, factor_df, on='subject_id', how='inner')
    logger.log("full_metrics_generated", rows=len(merged))
    return merged

def save_full_metrics(
    df: pd.DataFrame,
    output_path: str = "data/analysis/full_metrics.csv"
):
    """
    Save full metrics DataFrame to CSV.
    
    Args:
        df: Combined metrics DataFrame
        output_path: Path for output file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.log("full_metrics_saved", path=output_path, rows=len(df))

def run_correlations_with_fd_covariate(
    df: pd.DataFrame,
    metric_columns: List[str] = None,
    fd_column: str = 'MeanFD',
    motor_score_column: str = 'motor_score'
) -> pd.DataFrame:
    """
    Perform Spearman/Pearson correlation with FD covariate.
    
    Args:
        df: DataFrame with metrics and behavioral data
        metric_columns: List of metric columns to test
        fd_column: Name of FD column for covariate control
        motor_score_column: Name of motor score column
        
    Returns:
        DataFrame with correlation results
    """
    if metric_columns is None:
        metric_columns = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    results = []
    
    for metric in metric_columns:
        if metric not in df.columns:
            continue
        
        x = df[metric].dropna()
        y = df[motor_score_column].loc[x.index].dropna()
        
        if len(x) < 3:
            continue
        
        # Align indices
        common_idx = x.index.intersection(y.index)
        x = x.loc[common_idx]
        y = y.loc[common_idx]
        
        # Calculate correlation
        r, p_value = stats.pearsonr(x, y)
        
        # Store result
        results.append({
            'metric_name': metric,
            'r': r,
            'p': p_value,
            'n': len(x),
            'covariate_controlled': False  # Simple correlation, not partial
        })
    
    result_df = pd.DataFrame(results)
    logger.log("correlations_run", n_tests=len(result_df))
    return result_df

def apply_fdr_correction(
    results_df: pd.DataFrame,
    p_column: str = 'p',
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        results_df: DataFrame with p-values
        p_column: Name of p-value column
        alpha: Significance threshold
        
    Returns:
        DataFrame with corrected p-values and significance
    """
    if len(results_df) == 0:
        return results_df
    
    p_values = results_df[p_column].values
    rejected, q_values, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    results_df['q'] = q_values
    results_df['significant'] = rejected
    
    logger.log("fdr_correction_applied", n_significant=rejected.sum(), alpha=alpha)
    return results_df

def log_significant_correlations(
    results_df: pd.DataFrame,
    threshold: float = 0.3
):
    """
    Log correlation results where |r| > threshold.
    
    Args:
        results_df: DataFrame with correlation results
        threshold: Absolute r threshold for logging
    """
    significant = results_df[results_df['r'].abs() > threshold]
    
    for _, row in significant.iterrows():
        logger.log(
            "significant_correlation_detected",
            metric=row['metric_name'],
            r=row['r'],
            p=row['p'],
            q=row.get('q', None),
            threshold=threshold
        )
    
    logger.log("significant_correlations_logged", count=len(significant), threshold=threshold)
    return significant

def main():
    """Main entry point for correlation analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run correlation analysis on network metrics")
    parser.add_argument("--input", default="data/processed/aggregated_metrics.csv", help="Input metrics file")
    parser.add_argument("--output-dir", default="data/analysis", help="Output directory")
    
    args = parser.parse_args()
    
    # Load data
    metrics_df = load_metrics_data(args.input)
    
    # Perform PCA
    pca, factor_df = perform_pca_on_metrics(metrics_df)
    
    # Save PCA results
    loadings_path = os.path.join(args.output_dir, "pca_loadings.csv")
    scores_path = os.path.join(args.output_dir, "factor_scores.csv")
    save_pca_results(pca, factor_df, loadings_path, scores_path)
    
    # Generate full metrics
    full_df = generate_full_metrics(metrics_df, factor_df)
    full_path = os.path.join(args.output_dir, "full_metrics.csv")
    save_full_metrics(full_df, full_path)
    
    # Run correlations
    corr_results = run_correlations_with_fd_covariate(full_df)
    
    # Apply FDR correction
    corr_results = apply_fdr_correction(corr_results)
    
    # Log significant correlations
    log_significant_correlations(corr_results)
    
    # Save correlation results
    corr_path = os.path.join(args.output_dir, "correlation_results.csv")
    corr_results.to_csv(corr_path, index=False)
    
    print(f"Analysis complete. Results saved to {args.output_dir}")

if __name__ == "__main__":
    main()
