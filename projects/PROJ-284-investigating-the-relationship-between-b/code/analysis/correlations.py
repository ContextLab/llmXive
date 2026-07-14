"""
Correlation analysis module for US2.
Implements PCA, FDR correction, and correlation with FD covariate.
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
from sklearn.preprocessing import StandardScaler

from code.logging_config import get_logger
from code.utils.memory_monitor import get_available_memory, calculate_dynamic_batch_size

logger = get_logger(__name__)

def get_available_memory() -> float:
    """Get available memory in GB."""
    return get_available_memory()

def calculate_dynamic_batch_size(total_items: int, memory_limit_gb: float = 7.0) -> int:
    """Calculate batch size based on memory constraints."""
    return calculate_dynamic_batch_size(memory_limit_gb)

def load_metrics_data(filepath: str) -> pd.DataFrame:
    """Load aggregated metrics from CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.log("load_metrics_data", path=str(path), rows=len(df))
    return df

def perform_pca_on_metrics(df: pd.DataFrame, n_components: int = 2) -> Tuple[PCA, pd.DataFrame, pd.DataFrame]:
    """
    Perform PCA on network metrics.
    Input: DataFrame with columns [modularity, global_efficiency, participation_coef, within_module_degree]
    Output: PCA object, loadings DataFrame, factor scores DataFrame
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    if not all(col in df.columns for col in metric_cols):
        missing = [c for c in metric_cols if c not in df.columns]
        raise ValueError(f"Missing required metric columns: {missing}")

    X = df[metric_cols].dropna()
    if X.empty:
        raise ValueError("No valid data for PCA after dropping NaNs")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(X_scaled)

    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=[f'component_{i+1}' for i in range(n_components)],
        index=metric_cols
    )

    scores_df = pd.DataFrame(scores, columns=[f'pca_factor_{i+1}' for i in range(n_components)])
    scores_df['subject_id'] = df.loc[X.index, 'subject_id'].values

    logger.log("perform_pca_on_metrics", n_components=n_components, explained_variance=pca.explained_variance_ratio_.tolist())
    return pca, loadings_df, scores_df

def save_pca_results(loadings_df: pd.DataFrame, scores_df: pd.DataFrame, output_dir: str = "data/analysis") -> None:
    """Save PCA loadings and factor scores to CSV."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    loadings_path = output_path / "pca_loadings.csv"
    scores_path = output_path / "factor_scores.csv"

    loadings_df.to_csv(loadings_path, index=True)
    scores_df.to_csv(scores_path, index=False)

    logger.log("save_pca_results", loadings=str(loadings_path), scores=str(scores_path))

def generate_full_metrics(raw_metrics_df: pd.DataFrame, pca_scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge individual metric columns with PCA factor scores.
    Ensures FR-005 (FDR on individual metrics) and FR-004 (report generation) have access to all data.
    """
    if 'subject_id' not in raw_metrics_df.columns:
        raise ValueError("raw_metrics_df must contain 'subject_id'")
    if 'subject_id' not in pca_scores_df.columns:
        raise ValueError("pca_scores_df must contain 'subject_id'")

    merged = pd.merge(raw_metrics_df, pca_scores_df, on='subject_id', how='inner')
    logger.log("generate_full_metrics", rows_before=len(raw_metrics_df), rows_after=len(merged))
    return merged

def save_full_metrics(df: pd.DataFrame, filepath: str = "data/analysis/full_metrics.csv") -> None:
    """Save full metrics DataFrame to CSV."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.log("save_full_metrics", path=str(path), rows=len(df))

def run_correlations_with_fd_covariate(df: pd.DataFrame, metric_cols: List[str], fd_col: str = "MeanFD") -> pd.DataFrame:
    """
    Perform Spearman/Pearson correlation with FD covariate.
    Applies partial correlation to control for FD.
    Output: DataFrame with metric_name, r, p, q, significant, covariate_controlled
    """
    if fd_col not in df.columns:
        raise ValueError(f"FD column '{fd_col}' not found in dataframe")

    results = []
    for metric in metric_cols:
        if metric not in df.columns:
            continue

        # Partial correlation: r_xy.z
        x = df[metric].values
        y = df.get("motor_score", df.get("Subject", np.arange(len(df)))).values # Fallback if motor_score missing
        z = df[fd_col].values

        # Simple partial correlation calculation using residuals
        # Regress x on z
        slope_x, intercept_x, r_val_x, p_val_x, std_err_x = stats.linregress(z, x)
        resid_x = x - (slope_x * z + intercept_x)

        # Regress y on z
        slope_y, intercept_y, r_val_y, p_val_y, std_err_y = stats.linregress(z, y)
        resid_y = y - (slope_y * z + intercept_y)

        # Correlate residuals
        r, p, _ = stats.pearsonr(resid_x, resid_y)

        results.append({
            "metric_name": metric,
            "r": r,
            "p": p,
            "q": np.nan, # Will be filled by FDR
            "significant": False,
            "covariate_controlled": True
        })

    results_df = pd.DataFrame(results)
    logger.log("run_correlations_with_fd_covariate", count=len(results_df))
    return results_df

def apply_fdr_correction(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Implement Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: Array of uncorrected p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        Tuple of (adjusted p-values, boolean array of significance)
    """
    if len(p_values) == 0:
        return np.array([]), np.array([], dtype=bool)

    m = len(p_values)
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # Calculate BH critical values: (i / m) * alpha
    # i ranges from 1 to m
    ranks = np.arange(1, m + 1)
    bh_thresholds = (ranks / m) * alpha

    # Determine significance: p <= threshold
    # We need to find the largest k such that p(k) <= (k/m)*alpha
    # Then all p(i) for i <= k are significant.
    # A simpler vectorized check for adjusted p-values:
    # q_i = p_i * m / rank_i
    # Then enforce monotonicity: q_i = min(q_i, q_{i+1}) working backwards.

    adjusted_p = sorted_p * m / ranks

    # Enforce monotonicity (cumulative min from the end)
    for i in range(m - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i+1])

    # Clip to 1.0
    adjusted_p = np.clip(adjusted_p, 0, 1.0)

    # Restore original order
    final_adjusted_p = np.empty(m)
    final_adjusted_p[sorted_indices] = adjusted_p

    significant = final_adjusted_p <= alpha

    logger.log("apply_fdr_correction", m=m, alpha=alpha, significant_count=np.sum(significant))
    return final_adjusted_p, significant

def save_correlation_results(results_df: pd.DataFrame, filepath: str = "data/analysis/correlation_results.csv") -> None:
    """Save correlation results to CSV."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(path, index=False)
    logger.log("save_correlation_results", path=str(path))

def main() -> None:
    """
    Main entry point for US2 analysis.
    Orchestrates PCA, FDR, and correlation steps.
    """
    logger.log("main", step="US2 Analysis Start")

    # 1. Load metrics (Assuming aggregated metrics are ready from T021/T022)
    # Path must be consistent with T017/T022 output
    metrics_path = "data/processed/aggregated_metrics.csv"
    if not os.path.exists(metrics_path):
        # Fallback for testing if file doesn't exist yet, but in real run it must exist
        logger.log("main", error=f"Metrics file not found at {metrics_path}", status="waiting")
        # In a real pipeline, we might raise or exit. For this task, we assume it exists or is created upstream.
        # If this is run standalone for testing, we might need to mock, but T025 requires real data logic.
        # We will proceed assuming the file exists as per the pipeline flow.
        return

    df = load_metrics_data(metrics_path)

    # 2. Perform PCA
    pca, loadings_df, scores_df = perform_pca_on_metrics(df)
    save_pca_results(loadings_df, scores_df)

    # 3. Generate Full Metrics
    full_metrics = generate_full_metrics(df, scores_df)
    save_full_metrics(full_metrics)

    # 4. Run Correlations with FD
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    corr_results = run_correlations_with_fd_covariate(full_metrics, metric_cols)

    # 5. Apply FDR Correction (T025 Implementation)
    p_vals = corr_results['p'].values
    adj_p_vals, significant_mask = apply_fdr_correction(p_vals)

    corr_results['q'] = adj_p_vals
    corr_results['significant'] = significant_mask

    # 6. Save Results
    save_correlation_results(corr_results)

    logger.log("main", status="completed", results_path="data/analysis/correlation_results.csv")
    print(f"Analysis complete. Results saved to data/analysis/correlation_results.csv")

if __name__ == "__main__":
    main()