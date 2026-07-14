from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from scipy import stats

from code.logging_config import get_logger

logger = get_logger(__name__)

def load_metrics_data(path: Path) -> pd.DataFrame:
    """Loads metrics data from a CSV file."""
    logger.log("load_metrics_data", path=str(path))
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    return pd.read_csv(path)

def run_correlations_with_fd_covariate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs Spearman/Pearson correlation with Framewise Displacement (FD) as a covariate.
    Returns a DataFrame of correlation results.
    """
    logger.log("run_correlations_with_fd_covariate", shape=df.shape)
    
    results = []
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    for col in metric_cols:
        if col not in df.columns:
            continue
        
        # Partial correlation with FD
        if 'fd' in df.columns:
            # Simple partial correlation: correlate col with motor_score, controlling for fd
            # We use scipy's partial correlation if available, or manual calculation
            # For simplicity, we use partial correlation from pingouin if available, else manual
            try:
                from pingouin import partial_corr
                res = partial_corr(data=df, x=col, y='motor_score', covar='fd')
                r = res['r'].values[0]
                p = res['p-val'].values[0]
            except ImportError:
                # Manual partial correlation
                # Correlate col with motor_score
                r1, p1 = stats.spearmanr(df[col], df['motor_score'])
                # Correlate col with fd
                r2, p2 = stats.spearmanr(df[col], df['fd'])
                # Correlate motor_score with fd
                r3, p3 = stats.spearmanr(df['motor_score'], df['fd'])
                
                # Partial correlation formula
                if (1 - r2**2) * (1 - r3**2) == 0:
                    r = 0.0
                    p = 1.0
                else:
                    r = (r1 - r2 * r3) / np.sqrt((1 - r2**2) * (1 - r3**2))
                    # Approximate p-value
                    n = len(df)
                    t_stat = r * np.sqrt((n - 3) / (1 - r**2))
                    p = 2 * (1 - stats.t.cdf(abs(t_stat), n - 3))
        else:
            # No FD, just simple correlation
            r, p = stats.spearmanr(df[col], df['motor_score'])
        
        results.append({
            'metric_name': col,
            'r': r,
            'p': p,
            'significant': p < 0.05
        })
    
    return pd.DataFrame(results)

def apply_fdr_correction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies Benjamini-Hochberg FDR correction to p-values.
    """
    logger.log("apply_fdr_correction", shape=df.shape)
    
    p_vals = df['p'].values
    n = len(p_vals)
    sorted_indices = np.argsort(p_vals)
    sorted_p_vals = p_vals[sorted_indices]
    
    fdr_p_vals = np.zeros(n)
    for i, p in enumerate(sorted_p_vals):
        fdr_p_vals[sorted_indices[i]] = min(p * n / (i + 1), 1.0)
    
    df['q'] = fdr_p_vals
    df['significant_fdr'] = df['q'] < 0.05
    
    return df

def log_significant_correlations(df: pd.DataFrame):
    """Logs significant correlations."""
    logger.log("log_significant_correlations", count=len(df[df['significant_fdr']]))
    for _, row in df.iterrows():
        if row['significant_fdr']:
            logger.log("significant_correlation", metric=row['metric_name'], r=row['r'], q=row['q'])

def run_pca_on_metrics(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Runs PCA on the network metrics.
    Returns loadings and factor scores.
    """
    logger.log("run_pca_on_metrics", shape=df.shape)
    
    from sklearn.decomposition import PCA
    
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    available_cols = [c for c in metric_cols if c in df.columns]
    
    if not available_cols:
        return np.array([]), np.array([])
    
    X = df[available_cols].fillna(0)
    pca = PCA(n_components=2)
    scores = pca.fit_transform(X)
    loadings = pca.components_
    
    return loadings, scores

def generate_full_metrics(metrics_df: pd.DataFrame, pca_scores: np.ndarray, output_path: Path):
    """
    Generates the full metrics CSV with PCA scores.
    """
    logger.log("generate_full_metrics", shape=metrics_df.shape)
    
    df_full = metrics_df.copy()
    df_full['pca_factor_1'] = pca_scores[:, 0]
    df_full['pca_factor_2'] = pca_scores[:, 1]
    
    df_full.to_csv(output_path / "full_metrics.csv", index=False)
    logger.log("generate_full_metrics", status="completed", path=str(output_path))

def main():
    """
    Main entry point for the correlations module.

    This function orchestrates the correlation analysis process, including
    loading data, running correlations, applying FDR correction, and generating outputs.
    """
    logger.log("correlations_main", status="started")
    
    metrics_path = Path("data/processed/aggregated_metrics.csv")
    if not metrics_path.exists():
        logger.log("correlations_main", status="failed", error=f"Metrics file not found: {metrics_path}")
        return
    
    df = load_metrics_data(metrics_path)
    
    # Run correlations
    corr_df = run_correlations_with_fd_covariate(df)
    
    # Apply FDR
    corr_df = apply_fdr_correction(corr_df)
    
    # Log results
    log_significant_correlations(corr_df)
    
    # Save correlation results
    corr_df.to_csv("data/analysis/correlations.csv", index=False)
    
    # Run PCA
    loadings, scores = run_pca_on_metrics(df)
    
    # Save PCA results
    if len(scores) > 0:
        pca_df = pd.DataFrame(scores, columns=['pca_factor_1', 'pca_factor_2'])
        pca_df.insert(0, 'subject_id', df['subject_id'])
        pca_df.to_csv("data/analysis/factor_scores.csv", index=False)
        
        loadings_df = pd.DataFrame(loadings, columns=['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree'])
        loadings_df.index = ['component_1', 'component_2']
        loadings_df.to_csv("data/analysis/pca_loadings.csv")
        
        # Generate full metrics
        generate_full_metrics(df, scores, Path("data/analysis"))
    
    logger.log("correlations_main", status="completed")

if __name__ == "__main__":
    main()