"""
Correlation analysis module for US2.
Implements metric correlations, PCA, FDR, and threshold logging.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import numpy as np
from scipy import stats
from code.logging_config import get_logger

logger = get_logger(__name__)

# --- Data Loading ---

def load_metrics_data(input_path: str = "data/analysis/aggregated_metrics.csv") -> pd.DataFrame:
    """Load aggregated metrics from disk."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    df = pd.read_csv(path)
    logger.log("load_metrics_data", file=str(path), rows=len(df))
    return df

# --- PCA Implementation ---

def run_pca(df: pd.DataFrame, metric_cols: List[str], n_components: int = 2) -> Tuple[Any, pd.DataFrame]:
    """Run PCA on specified metric columns."""
    from sklearn.decomposition import PCA
    data = df[metric_cols].dropna()
    if len(data) == 0:
        raise ValueError("No valid data for PCA after dropping NaNs.")
    
    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(data)
    
    # Create scores dataframe with explicit column names
    score_cols = [f'pca_factor_{i+1}' for i in range(n_components)]
    scores_df = pd.DataFrame(scores, columns=score_cols)
    
    # Align index with original dataframe (dropna changed it)
    # We assume the caller handles index alignment or we re-merge later.
    # For this implementation, we return the scores aligned to the non-null rows.
    return pca, scores_df.reset_index(drop=True)

def compute_and_save_pca(df: pd.DataFrame, metric_cols: List[str], output_dir: str = "data/analysis") -> Tuple[str, str]:
    """Compute PCA and save loadings and scores."""
    pca, scores = run_pca(df, metric_cols)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Loadings
    loadings_df = pd.DataFrame(pca.components_.T, columns=[f'component_{i+1}' for i in range(pca.n_components_)])
    loadings_df.index = metric_cols
    loadings_path = output_path / "pca_loadings.csv"
    loadings_df.to_csv(loadings_path)
    logger.log("compute_and_save_pca", output=str(loadings_path), shape=loadings_df.shape)
    
    # Scores
    scores_path = output_path / "factor_scores.csv"
    # Ensure subject_id is included if present in original df
    if 'subject_id' in df.columns:
        # Align scores with original df rows (handling NaNs in metrics)
        valid_indices = df[metric_cols].notna().all(axis=1)
        scores_df_with_id = pd.DataFrame(scores, columns=[f'pca_factor_{i+1}' for i in range(pca.n_components_)])
        scores_df_with_id['subject_id'] = df.loc[valid_indices, 'subject_id'].values
        scores_df_with_id.to_csv(scores_path, index=False)
    else:
        scores.to_csv(scores_path, index=False)
    
    return str(loadings_path), str(scores_path)

# --- Merging Metrics and PCA ---

def merge_metrics_and_pca(metrics_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    """Merge raw metrics with PCA factor scores."""
    # Ensure subject_id is in both for merge
    if 'subject_id' in metrics_df and 'subject_id' in scores_df:
        merged = pd.merge(metrics_df, scores_df, on='subject_id', how='inner')
    elif 'subject_id' in metrics_df:
        # If scores_df doesn't have ID (unlikely if we generated it right), just concat
        # But we expect subject_id in scores_df from compute_and_save_pca
        merged = pd.concat([metrics_df, scores_df], axis=1)
    else:
        merged = pd.concat([metrics_df, scores_df], axis=1)
    
    logger.log("merge_metrics_and_pca", rows=len(merged))
    return merged

def create_full_metrics_output(
    metrics_path: str = "data/analysis/aggregated_metrics.csv",
    output_path: str = "data/analysis/full_metrics.csv"
) -> str:
    """Load metrics, run PCA, merge, and save full output."""
    df = load_metrics_data(metrics_path)
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    missing_cols = [c for c in metric_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required metric columns: {missing_cols}")
    
    _, scores_df = compute_and_save_pca(df, metric_cols)
    merged = merge_metrics_and_pca(df, scores_df)
    
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_path, index=False)
    logger.log("create_full_metrics_output", path=str(out_path), rows=len(merged))
    return str(out_path)

# --- Correlation Analysis ---

def partial_correlation(
    x: pd.Series,
    y: pd.Series,
    covariates: Optional[pd.DataFrame] = None
) -> Tuple[float, float]:
    """
    Calculate partial correlation between x and y, controlling for covariates.
    Returns (r, p_value).
    """
    if covariates is None or covariates.empty:
        r, p = stats.pearsonr(x, y)
        return float(r), float(p)
    
    # Residualize x and y against covariates
    from sklearn.linear_model import LinearRegression
    
    X = covariates.values
    # Add intercept
    X = np.c_[np.ones(len(X)), X]
    
    model_x = LinearRegression().fit(X, x.values)
    res_x = x.values - model_x.predict(X)
    
    model_y = LinearRegression().fit(X, y.values)
    res_y = y.values - model_y.predict(X)
    
    r, p = stats.pearsonr(res_x, res_y)
    return float(r), float(p)

def run_metric_correlations(
    df: pd.DataFrame,
    target_col: str = 'motor_score',
    metric_cols: List[str] = None,
    covariate_col: str = 'fd'
) -> pd.DataFrame:
    """
    Run correlations for each metric against target, controlling for covariate.
    """
    if metric_cols is None:
        metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    results = []
    for col in metric_cols:
        if col not in df.columns or target_col not in df.columns:
            continue
        
        x = df[col].dropna()
        y = df[target_col].reindex(x.index)
        cov = None
        if covariate_col in df.columns:
            cov = df[covariate_col].reindex(x.index).to_frame()
            # Drop rows where covariate is NaN
            valid_mask = cov.notna().all(axis=1)
            x = x[valid_mask]
            y = y[valid_mask]
            cov = cov[valid_mask]
        
        if len(x) < 3:
            continue
            
        r, p = partial_correlation(x, y, cov)
        results.append({
            'metric': col,
            'r': r,
            'p': p
        })
    
    return pd.DataFrame(results)

def apply_fdr_correction(df: pd.DataFrame, p_col: str = 'p', q_col: str = 'q') -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction."""
    p_values = df[p_col].values
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    ranks = np.arange(1, n + 1)
    q_values = (sorted_p * n) / ranks
    q_values = np.minimum.accumulate(q_values[::-1])[::-1]
    q_values = np.clip(q_values, 0, 1)
    
    df[q_col] = 0.0
    df.loc[sorted_indices, q_col] = q_values
    df['significant'] = df[q_col] < 0.05
    
    logger.log("apply_fdr_correction", n=len(df), significant=df['significant'].sum())
    return df

# --- T027: Correlation Threshold Logging ---

def log_threshold_correlations(correlation_results: pd.DataFrame, threshold: float = 0.3) -> None:
    """
    Log correlations where absolute r > threshold.
    This satisfies T027: Implement correlation threshold logging (r > 0.3).
    """
    if correlation_results.empty:
        logger.log("log_threshold_correlations", message="No correlation results to log.")
        return

    significant_correlations = correlation_results[
        correlation_results['r'].abs() > threshold
    ]
    
    if significant_correlations.empty:
        logger.log("log_threshold_correlations", 
                   threshold=threshold, 
                   message=f"No correlations found with |r| > {threshold}.")
        return

    for _, row in significant_correlations.iterrows():
        metric = row['metric']
        r_val = row['r']
        p_val = row.get('p', 'N/A')
        q_val = row.get('q', 'N/A')
        
        # Log the specific threshold breach
        logger.log("CORRELATION_THRESHOLD_EXCEEDED",
                   metric=metric,
                   r=r_val,
                   p=p_val,
                   q=q_val,
                   threshold=threshold,
                   direction="positive" if r_val > 0 else "negative")

def main():
    """Main entry point for running the correlation analysis pipeline."""
    try:
        # 1. Load Data
        metrics_df = load_metrics_data("data/analysis/aggregated_metrics.csv")
        
        # 2. Run PCA (T023a)
        metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
        _, scores_df = compute_and_save_pca(metrics_df, metric_cols)
        
        # 3. Merge (T023b)
        full_df = merge_metrics_and_pca(metrics_df, scores_df)
        full_df.to_csv("data/analysis/full_metrics.csv", index=False)
        
        # 4. Run Correlations (T024)
        corr_df = run_metric_correlations(full_df, target_col='motor_score', metric_cols=metric_cols)
        
        # 5. FDR Correction (T025)
        corr_df = apply_fdr_correction(corr_df)
        
        # 6. Log Thresholds (T027)
        log_threshold_correlations(corr_df, threshold=0.3)
        
        # Save final correlation table
        corr_df.to_csv("data/analysis/correlation_results.csv", index=False)
        
        logger.log("main", status="success", output_files=["data/analysis/full_metrics.csv", "data/analysis/correlation_results.csv"])
        
    except Exception as e:
        logger.log("main", status="failed", error=str(e))
        raise

# Helper for batch processing if needed (T028 placeholder structure)
def calculate_batch_size_for_matrix_computation(memory_limit_gb: float = 7.0) -> int:
    """Estimate batch size for matrix operations."""
    # Placeholder for memory management logic
    return 50

def process_metrics_in_batches(df: pd.DataFrame, batch_size: int = 50) -> pd.DataFrame:
    """Process metrics in batches."""
    return df # Placeholder for actual batch logic

if __name__ == "__main__":
    main()