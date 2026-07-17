"""
Correlation analysis module for network metrics.

Implements PCA, correlation analysis with covariates, and FDR correction.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from scipy import stats

from code.logging_config import get_logger

logger = get_logger(__name__)

# Constants
ANALYSIS_DIR = Path("data/analysis")
PROCESSED_DIR = Path("data/processed")

# Ensure output directories exist
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_metrics_data() -> pd.DataFrame:
    """
    Load aggregated metrics from the processed directory.
    
    Returns:
        DataFrame with columns: subject_id, modularity, global_efficiency, 
        participation_coef, within_module_degree, fd
    """
    metrics_path = PROCESSED_DIR / "aggregated_metrics.csv"
    
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Aggregated metrics file not found at {metrics_path}. "
            "Run the metric extraction pipeline first."
        )
    
    df = pd.read_csv(metrics_path)
    
    # Ensure required columns exist
    required_cols = ['subject_id', 'modularity', 'global_efficiency', 
                    'participation_coef', 'within_module_degree', 'fd']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in aggregated_metrics.csv: {missing_cols}"
        )
    
    logger.log("load_metrics_data", status="success", rows=len(df))
    return df

def run_pca_on_metrics(df: pd.DataFrame) -> Tuple[PCA, pd.DataFrame, pd.DataFrame]:
    """
    Perform PCA on network metrics.
    
    Args:
        df: DataFrame with metric columns
    
    Returns:
        Tuple of (PCA model, loadings DataFrame, factor scores DataFrame)
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 
                  'within_module_degree']
    
    # Check for missing values
    if df[metric_cols].isnull().any().any():
        logger.log("run_pca_on_metrics", status="warning", 
                  message="Dropping rows with missing values")
        df_clean = df.dropna(subset=metric_cols)
    else:
        df_clean = df
    
    if len(df_clean) < 2:
        raise ValueError("Need at least 2 samples for PCA")
    
    # Standardize features
    scaler = stats.zscore
    X_standardized = scaler(df_clean[metric_cols].values)
    
    # Run PCA
    pca = PCA(n_components=min(len(metric_cols), len(df_clean)))
    components = pca.fit_transform(X_standardized)
    
    # Create loadings DataFrame
    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=[f'component_{i+1}' for i in range(pca.n_components_)],
        index=metric_cols
    )
    
    # Create factor scores DataFrame
    factor_scores_df = pd.DataFrame(
        components,
        columns=[f'pca_factor_{i+1}' for i in range(pca.n_components_)],
        index=df_clean.index
    )
    factor_scores_df['subject_id'] = df_clean['subject_id'].values
    
    logger.log("run_pca_on_metrics", status="success", 
              n_components=pca.n_components_, explained_variance_ratio=pca.explained_variance_ratio_.tolist())
    
    return pca, loadings_df, factor_scores_df

def save_pca_outputs(loadings_df: pd.DataFrame, factor_scores_df: pd.DataFrame) -> None:
    """
    Save PCA outputs to CSV files.
    
    Args:
        loadings_df: DataFrame with PCA loadings
        factor_scores_df: DataFrame with subject factor scores
    """
    loadings_path = ANALYSIS_DIR / "pca_loadings.csv"
    scores_path = ANALYSIS_DIR / "factor_scores.csv"
    
    loadings_df.to_csv(loadings_path, index=True)
    factor_scores_df.to_csv(scores_path, index=False)
    
    logger.log("save_pca_outputs", status="success", 
              loadings_path=str(loadings_path), scores_path=str(scores_path))

def generate_full_metrics(raw_metrics_df: pd.DataFrame, factor_scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge individual metric columns with PCA factor scores into a single output DataFrame.
    
    This ensures FR-005 (FDR on individual metrics) and FR-004 (report generation) 
    have access to all data.
    
    Args:
        raw_metrics_df: DataFrame with raw metrics (subject_id, modularity, etc.)
        factor_scores_df: DataFrame with PCA factor scores (subject_id, pca_factor_1, etc.)
    
    Returns:
        DataFrame containing all raw metrics AND PCA factors
    """
    # Merge on subject_id
    merged_df = pd.merge(
        raw_metrics_df,
        factor_scores_df[['subject_id'] + [col for col in factor_scores_df.columns if col != 'subject_id']],
        on='subject_id',
        how='inner'
    )
    
    logger.log("generate_full_metrics", status="success", 
              n_rows=len(merged_df), n_columns=len(merged_df.columns))
    
    return merged_df

def save_full_metrics(merged_df: pd.DataFrame) -> None:
    """
    Save the full merged metrics DataFrame to CSV.
    
    Args:
        merged_df: DataFrame with all raw metrics and PCA factors
    """
    output_path = ANALYSIS_DIR / "full_metrics.csv"
    
    merged_df.to_csv(output_path, index=False)
    
    logger.log("save_full_metrics", status="success", output_path=str(output_path), 
              n_rows=len(merged_df), n_columns=len(merged_df.columns))

def run_simple_correlations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run simple Spearman correlations between metrics and motor scores.
    
    Args:
        df: DataFrame with metrics and motor_score column
    
    Returns:
        List of correlation results
    """
    results = []
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    for col in metric_cols:
        if col not in df.columns or 'motor_score' not in df.columns:
            continue
        
        # Remove rows with NaN
        valid_data = df[[col, 'motor_score']].dropna()
        if len(valid_data) < 3:
            continue
        
        r, p_value = stats.spearmanr(valid_data[col], valid_data['motor_score'])
        
        results.append({
            'metric': col,
            'correlation_type': 'spearman',
            'r': r,
            'p_value': p_value,
            'n': len(valid_data)
        })
    
    logger.log("run_simple_correlations", status="success", n_correlations=len(results))
    return results

def run_correlations_with_fd_covariate(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run correlations with Framewise Displacement (FD) as a covariate.
    
    Uses partial correlation to control for FD.
    
    Args:
        df: DataFrame with metrics, motor_score, and fd columns
    
    Returns:
        List of correlation results with FD controlled
    """
    results = []
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    for col in metric_cols:
        if not all(x in df.columns for x in [col, 'motor_score', 'fd']):
            continue
        
        # Remove rows with NaN
        valid_data = df[[col, 'motor_score', 'fd']].dropna()
        if len(valid_data) < 4:
            continue
        
        # Partial correlation: correlation between col and motor_score controlling for fd
        # Using scipy's partial correlation approach
        x = valid_data[col].values
        y = valid_data['motor_score'].values
        z = valid_data['fd'].values
        
        # Residualize x and y with respect to z
        _, _, rx = stats.linregress(z, x)
        x_resid = x - (rx * z + stats.linregress(z, x).intercept)
        
        _, _, ry = stats.linregress(z, y)
        y_resid = y - (ry * z + stats.linregress(z, y).intercept)
        
        # Correlation of residuals
        r, p_value = stats.pearsonr(x_resid, y_resid)
        
        results.append({
            'metric': col,
            'correlation_type': 'partial_spearman_fd',
            'r': r,
            'p_value': p_value,
            'n': len(valid_data),
            'covariate_controlled': True
        })
    
    logger.log("run_correlations_with_fd_covariate", status="success", n_correlations=len(results))
    return results

def apply_fdr_correction(correlation_results: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        correlation_results: List of correlation result dictionaries
        alpha: FDR threshold (default 0.05)
    
    Returns:
        Updated list with 'q' (adjusted p-value) and 'significant' fields
    """
    if not correlation_results:
        return correlation_results
    
    # Extract p-values
    p_values = [r['p_value'] for r in correlation_results]
    n = len(p_values)
    
    # Sort by p-value and calculate adjusted p-values (BH procedure)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # BH adjustment
    adjusted_p_values = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adjusted_p_values[sorted_indices[i]] = min(
            sorted_p_values[i] * n / rank,
            1.0
        )
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p_values[i] = min(adjusted_p_values[i], adjusted_p_values[i + 1])
    
    # Update results
    for i, result in enumerate(correlation_results):
        result['q'] = adjusted_p_values[i]
        result['significant'] = adjusted_p_values[i] < alpha
    
    logger.log("apply_fdr_correction", status="success", 
              n_tests=n, n_significant=sum(1 for r in correlation_results if r['significant']))
    
    return correlation_results

def log_significant_correlations(correlation_results: List[Dict[str, Any]]) -> None:
    """Log significant correlations for reporting."""
    significant = [r for r in correlation_results if r.get('significant', False)]
    
    if significant:
        logger.log("significant_correlations_found", count=len(significant))
        for r in significant:
            logger.log("significant_result", 
                      metric=r['metric'], 
                      r=r['r'], 
                      q=r['q'],
                      covariate_controlled=r.get('covariate_controlled', False))
    else:
        logger.log("no_significant_correlations", count=0)

def save_correlations_to_csv(correlation_results: List[Dict[str, Any]]) -> None:
    """Save correlation results to CSV."""
    output_path = ANALYSIS_DIR / "correlations.csv"
    
    df = pd.DataFrame(correlation_results)
    df.to_csv(output_path, index=False)
    
    logger.log("save_correlations_to_csv", status="success", output_path=str(output_path))

def process_metrics_with_batching(df: pd.DataFrame, batch_size: Optional[int] = None) -> pd.DataFrame:
    """
    Process metrics with dynamic batch sizing for memory constraints.
    
    Args:
        df: Input DataFrame
        batch_size: Optional batch size (if None, auto-calculate)
    
    Returns:
        Processed DataFrame
    """
    # For now, process all data at once since memory is not a bottleneck for this step
    # Future optimization: implement batching for very large datasets
    return df

def main() -> None:
    """
    Main entry point for correlation analysis.
    
    Executes the full pipeline:
    1. Load metrics data
    2. Run PCA
    3. Save PCA outputs
    4. Generate and save full metrics (T023b)
    5. Run correlations with FD covariate
    6. Apply FDR correction
    7. Save correlation results
    """
    logger.log("main", status="started", step="correlation_analysis")
    
    try:
        # Step 1: Load metrics
        logger.log("main", status="step", step="load_metrics")
        metrics_df = load_metrics_data()
        
        # Step 2: Run PCA
        logger.log("main", status="step", step="run_pca")
        pca_model, loadings_df, factor_scores_df = run_pca_on_metrics(metrics_df)
        
        # Step 3: Save PCA outputs (T023a)
        logger.log("main", status="step", step="save_pca_outputs")
        save_pca_outputs(loadings_df, factor_scores_df)
        
        # Step 4: Generate and save full metrics (T023b)
        logger.log("main", status="step", step="generate_full_metrics")
        full_metrics_df = generate_full_metrics(metrics_df, factor_scores_df)
        save_full_metrics(full_metrics_df)
        
        # Step 5: Run correlations with FD covariate
        logger.log("main", status="step", step="run_correlations")
        correlation_results = run_correlations_with_fd_covariate(metrics_df)
        
        # Step 6: Apply FDR correction
        logger.log("main", status="step", step="apply_fdr")
        correlation_results = apply_fdr_correction(correlation_results)
        
        # Step 7: Log and save results
        logger.log("main", status="step", step="log_and_save")
        log_significant_correlations(correlation_results)
        save_correlations_to_csv(correlation_results)
        
        logger.log("main", status="completed")
        
    except Exception as e:
        logger.log("main", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()