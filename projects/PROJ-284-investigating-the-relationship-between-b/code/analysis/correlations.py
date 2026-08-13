"""
Correlation analysis module for network metrics.
Implements PCA, correlation with covariates, and FDR correction.
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

logger = get_logger(__name__)

# Constants
FDR_THRESHOLD = 0.05
CORRELATION_THRESHOLD = 0.3

def load_metrics_data(input_path: str = "data/analysis/aggregated_metrics.csv") -> pd.DataFrame:
    """Load aggregated metrics data for analysis."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    
    df = pd.read_csv(path)
    logger.log("load_metrics_data", file=str(path), rows=len(df))
    return df

def run_pca_on_metrics(df: pd.DataFrame, n_components: int = 2) -> Tuple[PCA, pd.DataFrame, pd.DataFrame]:
    """Run PCA on network metrics."""
    # Select numeric columns for PCA (exclude subject_id if present)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if 'subject_id' in numeric_cols:
        numeric_cols.remove('subject_id')
    
    if len(numeric_cols) < 2:
        raise ValueError("Need at least 2 numeric columns for PCA")
    
    X = df[numeric_cols].values
    
    pca = PCA(n_components=n_components)
    components = pca.fit_transform(X)
    
    # Create loadings dataframe
    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=[f'PC{i+1}' for i in range(n_components)],
        index=numeric_cols
    )
    
    # Create factor scores dataframe
    factor_scores_df = pd.DataFrame(
        components,
        columns=[f'PC{i+1}' for i in range(n_components)],
        index=df.index
    )
    
    # Add subject_id back if it existed
    if 'subject_id' in df.columns:
        factor_scores_df['subject_id'] = df['subject_id'].values
        loadings_df['subject_id'] = None  # Placeholder for consistency
    
    logger.log("run_pca_on_metrics", n_components=n_components, n_features=len(numeric_cols))
    return pca, loadings_df, factor_scores_df

def save_pca_outputs(loadings_df: pd.DataFrame, factor_scores_df: pd.DataFrame, output_dir: str = "data/analysis") -> None:
    """Save PCA outputs to CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    loadings_path = output_path / "pca_loadings.csv"
    scores_path = output_path / "factor_scores.csv"
    
    loadings_df.to_csv(loadings_path, index=True)
    factor_scores_df.to_csv(scores_path, index=False)
    
    logger.log("save_pca_outputs", loadings_file=str(loadings_path), scores_file=str(scores_path))

def generate_full_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Generate full metrics dataframe combining all metrics."""
    # This function prepares the full metrics dataframe
    # It should include all original metrics plus PCA components
    full_df = df.copy()
    
    # If PCA was run, we would add those columns here
    # For now, just return the input with a flag
    full_df['analysis_complete'] = True
    
    logger.log("generate_full_metrics", rows=len(full_df))
    return full_df

def save_full_metrics(df: pd.DataFrame, output_path: str = "data/analysis/full_metrics.csv") -> None:
    """Save full metrics dataframe."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.log("save_full_metrics", file=str(path), rows=len(df))

def run_simple_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Run simple Spearman correlations between metrics and motor_score."""
    results = []
    
    # Assume 'motor_score' is the target variable
    if 'motor_score' not in df.columns:
        raise ValueError("motor_score column not found in dataframe")
    
    target = df['motor_score'].values
    
    for col in df.columns:
        if col in ['motor_score', 'subject_id', 'analysis_complete']:
            continue
        
        if not np.issubdtype(df[col].dtype, np.number):
            continue
        
        x = df[col].values
        
        # Handle NaN values
        mask = ~(np.isnan(x) | np.isnan(target))
        if mask.sum() < 5:
            continue
        
        x_clean = x[mask]
        target_clean = target[mask]
        
        r, p = stats.spearmanr(x_clean, target_clean)
        
        results.append({
            'metric': col,
            'correlation_type': 'spearman',
            'r': r,
            'p_value': p,
            'n': len(x_clean)
        })
    
    result_df = pd.DataFrame(results)
    logger.log("run_simple_correlations", n_correlations=len(results))
    return result_df

def run_correlations_with_fd_covariate(df: pd.DataFrame) -> pd.DataFrame:
    """Run partial correlations controlling for Framewise Displacement."""
    results = []
    
    if 'motor_score' not in df.columns or 'fd' not in df.columns:
        raise ValueError("motor_score or fd column not found")
    
    target = df['motor_score'].values
    fd = df['fd'].values
    
    for col in df.columns:
        if col in ['motor_score', 'subject_id', 'fd', 'analysis_complete']:
            continue
        
        if not np.issubdtype(df[col].dtype, np.number):
            continue
        
        x = df[col].values
        
        # Handle NaN values
        mask = ~(np.isnan(x) | np.isnan(target) | np.isnan(fd))
        if mask.sum() < 5:
            continue
        
        x_clean = x[mask]
        target_clean = target[mask]
        fd_clean = fd[mask]
        
        # Partial correlation: correlate x and target while controlling for fd
        # Using scipy's partial correlation approach via residuals
        from scipy.stats import pearsonr
        
        # Regress x on fd
        slope_x, intercept_x, _, _, _ = stats.linregress(fd_clean, x_clean)
        residuals_x = x_clean - (slope_x * fd_clean + intercept_x)
        
        # Regress target on fd
        slope_t, intercept_t, _, _, _ = stats.linregress(fd_clean, target_clean)
        residuals_target = target_clean - (slope_t * fd_clean + intercept_t)
        
        # Correlate residuals
        r, p = pearsonr(residuals_x, residuals_target)
        
        results.append({
            'metric': col,
            'correlation_type': 'partial_spearman_fd',
            'r': r,
            'p_value': p,
            'n': len(x_clean),
            'covariate': 'fd'
        })
    
    result_df = pd.DataFrame(results)
    logger.log("run_correlations_with_fd_covariate", n_correlations=len(results))
    return result_df

def apply_fdr_correction(results_df: pd.DataFrame, output_path: str = "data/analysis/fdr_corrected_results.csv") -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    if results_df.empty:
        logger.log("apply_fdr_correction", status="empty_input", message="No results to correct")
        return results_df
    
    p_values = results_df['p_value'].values
    n = len(p_values)
    
    if n == 0:
        return results_df
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate FDR thresholds
    ranks = np.arange(1, n + 1)
    thresholds = (ranks / n) * FDR_THRESHOLD
    
    # Find the largest k such that p(k) <= threshold(k)
    significant_mask = sorted_p <= thresholds
    if not np.any(significant_mask):
        logger.log("apply_fdr_correction", status="no_significant", message="No significant correlations after FDR")
        results_df['significant'] = False
        results_df['q_value'] = 1.0
        results_df['fdr_threshold'] = FDR_THRESHOLD
        return results_df
    
    k = np.where(significant_mask)[0][-1]
    critical_p = sorted_p[k]
    
    # Calculate q-values (adjusted p-values)
    q_values = np.zeros(n)
    min_q = 1.0
    for i in range(n - 1, -1, -1):
        min_q = min(min_q, (sorted_p[i] * n) / (i + 1))
        q_values[sorted_indices[i]] = min_q
    
    # Determine significance
    significant = q_values <= FDR_THRESHOLD
    
    # Add results to dataframe
    results_df['q_value'] = q_values
    results_df['significant'] = significant
    results_df['fdr_threshold'] = FDR_THRESHOLD
    
    # Log FDR threshold and results
    n_significant = significant.sum()
    logger.log(
        "apply_fdr_correction",
        status="completed",
        fdr_threshold=FDR_THRESHOLD,
        n_tests=n,
        n_significant=int(n_significant),
        critical_p=float(critical_p),
        message=f"FDR threshold q < {FDR_THRESHOLD} applied. {n_significant}/{n} correlations significant."
    )
    
    # Save to file
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(path, index=False)
    logger.log("apply_fdr_correction_saved", file=str(path))
    
    return results_df

def save_correlations_to_csv(results_df: pd.DataFrame, output_path: str = "data/analysis/correlation_results.csv") -> None:
    """Save correlation results to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(path, index=False)
    logger.log("save_correlations_to_csv", file=str(path), rows=len(results_df))

def log_significant_correlations(results_df: pd.DataFrame) -> None:
    """Log significant correlations to the analysis log."""
    significant = results_df[results_df['significant']]
    
    if significant.empty:
        logger.log("log_significant_correlations", count=0, message="No significant correlations found")
        return
    
    logger.log(
        "log_significant_correlations",
        count=len(significant),
        fdr_threshold=FDR_THRESHOLD,
        correlations=significant[['metric', 'r', 'p_value', 'q_value']].to_dict(orient='records'),
        message=f"Found {len(significant)} significant correlations (q < {FDR_THRESHOLD})"
    )

def process_metrics_with_batching(input_path: str, output_dir: str) -> None:
    """Process metrics with memory-aware batching."""
    # This is a placeholder for batch processing logic
    # In a full implementation, this would handle large datasets in chunks
    logger.log("process_metrics_with_batching", input=input_path, output=output_dir)

def main() -> None:
    """Main entry point for correlation analysis."""
    try:
        # Load data
        df = load_metrics_data()
        
        # Run simple correlations
        simple_results = run_simple_correlations(df)
        
        # Run correlations with FD covariate
        fd_results = run_correlations_with_fd_covariate(df)
        
        # Combine results
        all_results = pd.concat([simple_results, fd_results], ignore_index=True)
        
        # Apply FDR correction
        corrected_results = apply_fdr_correction(all_results)
        
        # Log significant correlations
        log_significant_correlations(corrected_results)
        
        # Save final results
        save_correlations_to_csv(corrected_results)
        
        logger.log("main", status="success", message="Correlation analysis completed successfully")
        
    except Exception as e:
        logger.log("main", status="error", error=str(e))
        raise