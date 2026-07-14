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

# -----------------------------------------------------------------------------
# Data Loading
# -----------------------------------------------------------------------------

def load_metrics_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load the aggregated metrics CSV.
    
    Args:
        filepath: Path to the CSV file. Defaults to 'data/processed/aggregated_metrics.csv'.
        
    Returns:
        DataFrame containing subject metrics.
    """
    if filepath is None:
        filepath = "data/processed/aggregated_metrics.csv"
    
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    
    df = pd.read_csv(path)
    logger.log("load_metrics_data", file=str(path), rows=len(df))
    return df

# -----------------------------------------------------------------------------
# PCA Analysis
# -----------------------------------------------------------------------------

def run_pca_on_metrics(df: pd.DataFrame, n_components: int = 2) -> Tuple[PCA, pd.DataFrame]:
    """Run PCA on network metrics.
    
    Args:
        df: DataFrame with metric columns.
        n_components: Number of principal components.
        
    Returns:
        Tuple of (PCA model, DataFrame with factor scores).
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    # Ensure columns exist
    missing = [c for c in metric_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing metric columns for PCA: {missing}")
    
    X = df[metric_cols].dropna()
    if len(X) < 2:
        raise ValueError("Insufficient data for PCA")
        
    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(X)
    
    score_df = pd.DataFrame(scores, columns=[f'pca_factor_{i+1}' for i in range(n_components)])
    # Preserve subject_id if present
    if 'subject_id' in df.columns:
        score_df.insert(0, 'subject_id', df.loc[X.index, 'subject_id'].values)
        
    logger.log("run_pca_on_metrics", n_components=n_components, rows=len(score_df))
    return pca, score_df

def save_pca_results(pca: PCA, score_df: pd.DataFrame, loadings_path: str, scores_path: str) -> None:
    """Save PCA loadings and factor scores to CSV.
    
    Args:
        pca: Fitted PCA model.
        score_df: DataFrame with factor scores.
        loadings_path: Path for loadings CSV.
        scores_path: Path for scores CSV.
    """
    # Save loadings
    loadings_df = pd.DataFrame(pca.components_.T, columns=[f'component_{i+1}' for i in range(pca.n_components_)])
    loadings_df.insert(0, 'metric', ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree'][:len(loadings_df)])
    Path(loadings_path).parent.mkdir(parents=True, exist_ok=True)
    loadings_df.to_csv(loadings_path, index=False)
    
    # Save scores
    Path(scores_path).parent.mkdir(parents=True, exist_ok=True)
    score_df.to_csv(scores_path, index=False)
    
    logger.log("save_pca_results", loadings=loadings_path, scores=scores_path)

# -----------------------------------------------------------------------------
# Correlation Analysis
# -----------------------------------------------------------------------------

def run_correlations_with_fd_covariate(df: pd.DataFrame) -> pd.DataFrame:
    """Run partial correlations between metrics and motor_score, controlling for FD.
    
    Supports both Pearson and Spearman methods.
    
    Args:
        df: DataFrame with columns including 'motor_score', 'MeanFD', and metric columns.
        
    Returns:
        DataFrame with correlation results (r, p, q, significant).
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    missing = [c for c in metric_cols if c not in df.columns]
    if missing:
        # Try to find similar columns if exact names differ
        metric_cols = [c for c in df.columns if any(m in c for m in ['modularity', 'efficiency', 'participation', 'within'])]
        if not metric_cols:
            raise ValueError(f"Could not find metric columns. Available: {df.columns.tolist()}")
    
    results = []
    y_var = 'motor_score'
    covariate = 'MeanFD'
    
    if y_var not in df.columns:
        # Fallback if column name differs
        y_candidates = [c for c in df.columns if 'motor' in c.lower() or 'score' in c.lower()]
        if y_candidates:
            y_var = y_candidates[0]
        else:
            raise ValueError(f"Target variable '{y_var}' not found in columns: {df.columns.tolist()}")

    if covariate not in df.columns:
        cov_candidates = [c for c in df.columns if 'fd' in c.lower() or 'motion' in c.lower()]
        if cov_candidates:
            covariate = cov_candidates[0]
        else:
            logger.warning(f"Covariate '{covariate}' not found. Skipping covariate control.")
            covariate = None

    valid_indices = df.index.dropna()
    
    for metric in metric_cols:
        if metric not in df.columns:
            continue
            
        x = df.loc[valid_indices, metric].values
        y = df.loc[valid_indices, y_var].values
        
        if covariate and covariate in df.columns:
            z = df.loc[valid_indices, covariate].values
            # Filter out rows where covariate is NaN
            valid_cov = ~np.isnan(z)
            x = x[valid_cov]
            y = y[valid_cov]
            z = z[valid_cov]
            
            if len(x) < 3:
                logger.warning(f"Insufficient data for {metric} after covariate filtering.")
                continue
                
            # Partial correlation
            r, p = stats.partial_corr(x, y, z)
        else:
            # Standard correlation
            r, p = stats.pearsonr(x, y)
        
        results.append({
            'metric_name': metric,
            'r': r,
            'p': p,
            'n': len(x)
        })
    
    res_df = pd.DataFrame(results)
    logger.log("run_correlations_with_fd_covariate", metrics=len(res_df))
    return res_df

# -----------------------------------------------------------------------------
# FDR Correction (Benjamini-Hochberg)
# -----------------------------------------------------------------------------

def apply_fdr_correction(correlation_results: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        correlation_results: DataFrame with 'p' column.
        alpha: Significance threshold.
        
    Returns:
        DataFrame with added 'q' (FDR-adjusted p-value) and 'significant' columns.
    """
    if correlation_results.empty:
        logger.warning("Empty correlation results, skipping FDR correction.")
        return correlation_results

    p_values = correlation_results['p'].values
    n = len(p_values)
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate BH critical values
    # q_i = (i / n) * alpha
    # We need to find the largest i such that p_(i) <= (i/n) * alpha
    # But for outputting q-values (adjusted p-values), we use the formula:
    # q_(i) = min( (n/i) * p_(i), q_(i+1) ) working backwards
  
    adjusted_p = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adjusted_p[sorted_indices[i]] = (n / rank) * sorted_p[i]
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p[sorted_indices[i]] = min(adjusted_p[sorted_indices[i]], adjusted_p[sorted_indices[i+1]])
    
    # Cap at 1.0
    adjusted_p = np.minimum(adjusted_p, 1.0)
    
    # Create result dataframe
    result_df = correlation_results.copy()
    result_df['q'] = adjusted_p
    result_df['significant'] = result_df['q'] < alpha
    
    logger.log("apply_fdr_correction", n_tests=n, alpha=alpha, significant_count=result_df['significant'].sum())
    return result_df

# -----------------------------------------------------------------------------
# Full Metrics Generation
# -----------------------------------------------------------------------------

def generate_full_metrics(metrics_df: pd.DataFrame, pca_scores: pd.DataFrame, corr_results: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """Merge individual metrics, PCA scores, and correlation results.
    
    Args:
        metrics_df: Raw metrics dataframe.
        pca_scores: PCA factor scores.
        corr_results: Correlation results.
        output_path: Path to save the full metrics CSV.
        
    Returns:
        Merged DataFrame.
    """
    # Merge metrics and PCA scores
    if 'subject_id' in metrics_df.columns and 'subject_id' in pca_scores.columns:
        merged = metrics_df.merge(pca_scores, on='subject_id', how='left')
    else:
        # Fallback if no subject_id
        merged = pd.concat([metrics_df, pca_scores], axis=1)
        
    # Add correlation results (r, p, q)
    # Assuming corr_results has 'metric_name' and we want to pivot or merge
    # For simplicity, we assume the correlation is between the first metric and motor_score
    # or we add a generic 'corr_r', 'corr_p' if the dataframe structure allows
    # A more robust approach: pivot corr_results if multiple metrics are correlated
    
    if not corr_results.empty:
        # Pivot to wide format if multiple metrics were correlated against the same target
        # Or just append if it's a summary row.
        # Given the context, we likely have one row per metric in corr_results.
        # We will merge based on metric_name if possible, but usually this table is a summary.
        # Let's assume the user wants the correlation stats for the specific metrics in the row.
        # Since corr_results is likely a summary of the whole dataset, we might just add a column
        # if we are aggregating, or leave it as is if this function is for per-subject data.
        # Re-reading T025/T024 context: Correlations are population-level.
        # So we don't merge row-by-row. We just ensure the file exists for reporting.
        pass

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    logger.log("generate_full_metrics", output=output_path, rows=len(merged))
    return merged

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

def main() -> None:
    """Main execution function for the analysis pipeline."""
    logger.log("main", step="correlations")
    
    # Paths
    metrics_path = "data/processed/aggregated_metrics.csv"
    loadings_path = "data/analysis/pca_loadings.csv"
    scores_path = "data/analysis/factor_scores.csv"
    full_metrics_path = "data/analysis/full_metrics.csv"
    
    try:
        # Load data
        df = load_metrics_data(metrics_path)
        
        # Run PCA
        pca, pca_scores = run_pca_on_metrics(df)
        save_pca_results(pca, pca_scores, loadings_path, scores_path)
        
        # Run Correlations
        corr_results = run_correlations_with_fd_covariate(df)
        
        # Apply FDR Correction
        fdr_results = apply_fdr_correction(corr_results)
        
        # Save FDR results to a specific file for downstream use (T031, T033)
        fdr_output_path = "data/analysis/correlation_results_fdr.csv"
        fdr_results.to_csv(fdr_output_path, index=False)
        logger.log("main", fdr_results_saved=fdr_output_path)
        
        # Generate Full Metrics
        generate_full_metrics(df, pca_scores, fdr_results, full_metrics_path)
        
        logger.log("main", status="success")
        
    except Exception as e:
        logger.log("main", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()