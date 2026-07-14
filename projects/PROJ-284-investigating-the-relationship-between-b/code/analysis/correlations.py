"""
Correlation analysis module for network metrics.
Implements PCA, correlation with FD, and FDR correction.
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


def load_metrics_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the aggregated metrics from the processed data file.
    Expected columns: subject_id, modularity, global_efficiency, participation_coef, within_module_degree.
    """
    if input_path is None:
        input_path = "data/processed/aggregated_metrics.csv"
    
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found at {input_path}. "
                                "Ensure T021/T022 have run and written data/processed/aggregated_metrics.csv.")
    
    df = pd.read_csv(path)
    
    # Validate required columns
    required_cols = ['subject_id', 'modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    # Clean data: drop rows with NaN in metric columns
    initial_len = len(df)
    df = df.dropna(subset=required_cols[1:])
    dropped = initial_len - len(df)
    if dropped > 0:
        logger.log("metrics_dropped", reason="NaN in metric columns", count=dropped)
    
    return df


def perform_pca_on_metrics(df: pd.DataFrame) -> Tuple[PCA, np.ndarray, np.ndarray]:
    """
    Perform PCA on the network metrics.
    
    Input: DataFrame with columns [modularity, global_efficiency, participation_coef, within_module_degree].
    Output: PCA model, loadings array, factor scores array.
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    X = df[metric_cols].values
    
    # Standardize data before PCA
    scaler = stats.zscore
    X_scaled = scaler(X, axis=0)
    
    # Perform PCA (keep 2 components for interpretability)
    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)
    
    # Loadings: correlation between original variables and components
    # For standardized data, loadings are roughly eigenvectors * sqrt(eigenvalues)
    # But sklearn components_ are the eigenvectors.
    # We calculate loadings as correlation between original (scaled) vars and components
    loadings = np.corrcoef(X_scaled.T, components.T)[:4, 4:]
    
    return pca, loadings, components


def save_pca_results(pca: PCA, loadings: np.ndarray, components: np.ndarray, 
                     subject_ids: List[str], metric_cols: List[str],
                     output_dir: str = "data/analysis") -> None:
    """
    Save PCA loadings and factor scores to CSV files.
    
    Output files:
    - data/analysis/pca_loadings.csv: columns component_1, component_2
    - data/analysis/factor_scores.csv: columns subject_id, pca_factor_1, pca_factor_2
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = Path(output_dir)
    
    # Save Loadings
    # Columns: variable name, component_1, component_2
    loading_df = pd.DataFrame({
        'variable': metric_cols,
        'component_1': loadings[:, 0],
        'component_2': loadings[:, 1]
    })
    loading_df.to_csv(output_path / "pca_loadings.csv", index=False)
    
    # Save Factor Scores
    # Columns: subject_id, pca_factor_1, pca_factor_2
    scores_df = pd.DataFrame({
        'subject_id': subject_ids,
        'pca_factor_1': components[:, 0],
        'pca_factor_2': components[:, 1]
    })
    scores_df.to_csv(output_path / "factor_scores.csv", index=False)
    
    logger.log("pca_results_saved", 
               loadings_file="pca_loadings.csv", 
               scores_file="factor_scores.csv", 
               n_subjects=len(subject_ids))


def merge_metrics_with_pca_scores(metrics_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the original metrics with the PCA factor scores.
    """
    merged = pd.merge(metrics_df, scores_df, on='subject_id', how='inner')
    logger.log("metrics_merged", n_rows=len(merged))
    return merged


def generate_full_metrics_output(merged_df: pd.DataFrame, output_path: str = "data/analysis/full_metrics.csv") -> None:
    """
    Save the merged DataFrame to full_metrics.csv.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    logger.log("full_metrics_saved", path=output_path)


def calculate_correlation_with_fd(metrics_df: pd.DataFrame, fd_col: str = "MeanFD") -> pd.DataFrame:
    """
    Calculate Spearman correlation between each metric and FD.
    Returns a DataFrame with metric_name, r, p, significant.
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    results = []
    
    for col in metric_cols:
        if col not in metrics_df.columns or fd_col not in metrics_df.columns:
            continue
        
        x = metrics_df[col].dropna()
        y = metrics_df[fd_col].loc[x.index]
        
        if len(x) < 3:
            continue
            
        r, p = stats.spearmanr(x, y)
        results.append({
            'metric_name': col,
            'r': r,
            'p': p,
            'significant': p < 0.05
        })
    
    return pd.DataFrame(results)


def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction.
    Returns a list of booleans indicating significance.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with indices
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    ranks = [i + 1 for i in range(n)]
    
    # Calculate critical values
    critical_values = [(r / n) * alpha for r in ranks]
    
    # Find the largest k where p(k) <= critical(k)
    significant = [False] * n
    for i in range(n - 1, -1, -1):
        idx, p_val = indexed[i]
        if p_val <= critical_values[i]:
            # All p-values with rank <= i are significant
            for j in range(i + 1):
                significant[indexed[j][0]] = True
            break
    
    return significant


def correct_correlations(correlation_results: pd.DataFrame) -> pd.DataFrame:
    """
    Apply FDR correction to correlation results.
    Adds 'q' (adjusted p-value) and 'significant_fdr' columns.
    """
    if 'p' not in correlation_results.columns:
        return correlation_results
    
    p_values = correlation_results['p'].tolist()
    is_sig = apply_benjamini_hochberg(p_values)
    
    # Calculate q-values (adjusted p-values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    q_values = np.zeros(n)
    min_q = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        q = (sorted_p[i] * n) / rank
        if q > min_q:
            q = min_q
        else:
            min_q = q
        q_values[sorted_indices[i]] = min_q
    
    correlation_results = correlation_results.copy()
    correlation_results['q'] = q_values
    correlation_results['significant_fdr'] = is_sig
    
    return correlation_results


def log_threshold_results(correlation_results: pd.DataFrame, threshold: float = 0.3) -> None:
    """
    Log correlations that exceed a certain threshold.
    """
    significant = correlation_results[correlation_results['significant_fdr']]
    strong = significant[abs(significant['r']) > threshold]
    logger.log("strong_correlations_found", 
               count=len(strong), 
               metrics=strong['metric_name'].tolist())


def load_metrics_with_batching(input_path: str, batch_size: int = 100) -> pd.DataFrame:
    """
    Load metrics with dynamic batch sizing (placeholder for memory constraints).
    For this task, we load normally as the dataset is small, but structure allows extension.
    """
    return load_metrics_data(input_path)


def compute_correlation_matrix_batched(df: pd.DataFrame, cols: List[str], batch_size: int = 100) -> np.ndarray:
    """
    Compute correlation matrix in batches if memory is constrained.
    """
    X = df[cols].values
    return np.corrcoef(X.T)


def main() -> None:
    """
    Main entry point for T023a: PCA on network metrics.
    1. Load aggregated metrics.
    2. Perform PCA.
    3. Save loadings and factor scores.
    4. Merge and save full metrics.
    """
    logger.log("pca_analysis_start")
    
    # 1. Load Data
    df = load_metrics_data()
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    # 2. Perform PCA
    pca, loadings, components = perform_pca_on_metrics(df)
    
    # 3. Save Results
    save_pca_results(
        pca, loadings, components, 
        subject_ids=df['subject_id'].tolist(),
        metric_cols=metric_cols
    )
    
    # 4. Merge and Save Full Metrics
    scores_df = pd.DataFrame({
        'subject_id': df['subject_id'],
        'pca_factor_1': components[:, 0],
        'pca_factor_2': components[:, 1]
    })
    merged_df = merge_metrics_with_pca_scores(df, scores_df)
    generate_full_metrics_output(merged_df)
    
    logger.log("pca_analysis_complete")


if __name__ == "__main__":
    main()
