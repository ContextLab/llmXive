from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from code.logging_config import get_logger

# Constants
CORRELATION_THRESHOLD = 0.3
FDR_ALPHA = 0.05
FD_THRESHOLD = 0.5

logger = get_logger(__name__)

def load_metrics_data(metrics_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Load the aggregated metrics data from CSV.
    Defaults to data/processed/aggregated_metrics.csv if not provided.
    """
    if metrics_path is None:
        metrics_path = Path("data/processed/aggregated_metrics.csv")
    else:
        metrics_path = Path(metrics_path)

    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    logger.log("load_metrics_data", path=str(metrics_path))
    df = pd.read_csv(metrics_path)
    logger.log("load_metrics_data_success", rows=len(df))
    return df

def calculate_correlation_batch_size() -> int:
    """
    Calculate the batch size for correlation computation based on memory constraints.
    For now, returns a safe default.
    """
    # Default batch size for correlation matrix computation
    return 100

def process_metrics_batch(df: pd.DataFrame, batch_size: int) -> List[pd.DataFrame]:
    """
    Split the dataframe into batches for processing.
    """
    batches = []
    for i in range(0, len(df), batch_size):
        batches.append(df.iloc[i:i + batch_size])
    return batches

def perform_pca_on_metrics(df: pd.DataFrame, metric_cols: List[str]) -> Tuple[PCA, pd.DataFrame]:
    """
    Perform PCA on the specified metric columns.
    Returns the fitted PCA model and the dataframe with added factor scores.
    """
    if not metric_cols or not all(col in df.columns for col in metric_cols):
        raise ValueError(f"Metric columns {metric_cols} not found in dataframe")

    logger.log("perform_pca_on_metrics", columns=metric_cols, n_samples=len(df))

    # Prepare data
    X = df[metric_cols].dropna()
    if X.empty:
        raise ValueError("No valid data for PCA after dropping NaNs")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)

    # Create results dataframe
    result_df = X.copy()
    for i in range(components.shape[1]):
        result_df[f'pca_factor_{i+1}'] = components[:, i]

    logger.log("pca_fit_success", n_components=2, explained_variance_ratio=list(pca.explained_variance_ratio_))
    return pca, result_df

def save_pca_results(pca: PCA, result_df: pd.DataFrame, loadings_path: Path, scores_path: Path) -> None:
    """
    Save PCA loadings and factor scores to CSV files.
    """
    # Save loadings
    loadings_df = pd.DataFrame(pca.components_.T, columns=[f'component_{i+1}' for i in range(pca.n_components_)])
    loadings_df.insert(0, 'metric', result_df.columns[:pca.n_components_].tolist()) # Approximate mapping
    # Actually, loadings should map metrics to components.
    # Let's create a proper long-format loadings table.
    loadings_records = []
    for i, metric in enumerate(result_df.columns[:len(pca.components_)]):
        for j, comp_name in enumerate([f'component_{k+1}' for k in range(pca.n_components_)]):
            loadings_records.append({
                'metric': metric,
                'component': comp_name,
                'loading': pca.components_[j, i] if j < len(pca.components_) and i < len(pca.components_[j]) else 0.0
            })
    
    loadings_out = pd.DataFrame(loadings_records)
    # If we can't perfectly map indices, we just save the components matrix as rows=metrics, cols=components
    # But the spec asked for columns: component_1, component_2.
    # Let's assume the first N rows of result_df (before pca columns) correspond to the metrics used.
    # A safer bet for the output format requested:
    loadings_simple = pd.DataFrame(pca.components_.T, columns=[f'component_{i+1}' for i in range(pca.n_components_)])
    loadings_simple.index = result_df.columns[:pca.n_components_] # This might fail if index mismatch, but we try.
    # Better: explicit index
    loadings_simple = pd.DataFrame(pca.components_.T, columns=[f'component_{i+1}' for i in range(pca.n_components_)])
    loadings_simple['metric'] = result_df.columns[:len(pca.components_)].tolist() # Assuming components_ shape matches metrics
    
    # Actually, pca.components_ shape is (n_components, n_features).
    # So rows are components, cols are features. We want rows=features, cols=components.
    loadings_final = pd.DataFrame(pca.components_.T, columns=[f'component_{i+1}' for i in range(pca.n_components_)])
    loadings_final.index.name = 'metric'
    loadings_final.to_csv(loadings_path)

    # Save factor scores
    # The result_df already has the scores. We need to save subject_id and scores.
    # Assuming 'subject_id' is in the original df.
    scores_cols = ['subject_id'] + [f'pca_factor_{i+1}' for i in range(pca.n_components_)]
    scores_out = result_df[scores_cols]
    scores_out.to_csv(scores_path, index=False)

    logger.log("save_pca_results", loadings_path=str(loadings_path), scores_path=str(scores_path))

def run_correlations_with_fd_covariate(df: pd.DataFrame, metric_cols: List[str], target_col: str = 'motor_score', fd_col: str = 'MeanFD') -> pd.DataFrame:
    """
    Run Spearman/Pearson correlations between each metric and the target,
    controlling for Framewise Displacement (FD) as a covariate using partial correlation logic
    (simplified as residual regression for this implementation) or just reporting bivariate
    if partial is too complex for the current data structure.
    
    We will implement a partial correlation: r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1-r_xz^2)(1-r_yz^2))
    """
    logger.log("run_correlations_with_fd_covariate", metrics=metric_cols, target=target_col, covariate=fd_col)

    results = []

    for metric in metric_cols:
        if metric not in df.columns or target_col not in df.columns or fd_col not in df.columns:
            continue

        x = df[metric].dropna()
        y = df[target_col].loc[x.index]
        z = df[fd_col].loc[x.index]

        if len(x) < 3:
            continue

        # Calculate bivariate correlations
        r_xy, p_xy = stats.pearsonr(x, y)
        r_xz, _ = stats.pearsonr(x, z)
        r_yz, _ = stats.pearsonr(y, z)

        # Partial correlation
        denom = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
        if denom == 0:
            r_partial = 0
            p_partial = 1.0
        else:
            r_partial = (r_xy - r_xz * r_yz) / denom
            # Approximate p-value for partial correlation
            # t = r * sqrt((n-2) / (1-r^2))
            n = len(x)
            t_stat = r_partial * np.sqrt((n - 2) / (1 - r_partial**2))
            p_partial = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))

        results.append({
            'metric': metric,
            'r': r_partial,
            'p': p_partial,
            'r_bivariate': r_xy,
            'p_bivariate': p_xy
        })

    results_df = pd.DataFrame(results)
    logger.log("correlations_complete", count=len(results_df))
    return results_df

def apply_fdr_correction(results_df: pd.DataFrame, alpha: float = FDR_ALPHA) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to the p-values.
    """
    logger.log("apply_fdr_correction", alpha=alpha, n_tests=len(results_df))

    if results_df.empty:
        return results_df

    df = results_df.copy()
    df['rank'] = df['p'].rank(method='min')
    n = len(df)
    
    # BH procedure
    df['threshold'] = (df['rank'] / n) * alpha
    df['significant'] = df['p'] <= df['threshold']
    
    # Also calculate q-values (adjusted p-values)
    # Sort by p-value
    df_sorted = df.sort_values('p')
    q = np.zeros(len(df_sorted))
    q[-1] = df_sorted['p'].iloc[-1]
    for i in range(len(df_sorted) - 2, -1, -1):
        q[i] = min(df_sorted['p'].iloc[i] * (n / (i + 1)), q[i+1])
    
    df['q'] = q
    df = df.sort_index() # Restore original order
    
    logger.log("fdr_complete", significant_count=df['significant'].sum())
    return df

def log_significant_correlations(results_df: pd.DataFrame, threshold: float = CORRELATION_THRESHOLD) -> None:
    """
    Log correlations that exceed the specified threshold (r > threshold).
    This fulfills T027.
    """
    if results_df.empty:
        logger.log("log_significant_correlations", count=0, reason="empty_results")
        return

    # Filter for significant correlations based on the threshold
    # Note: T027 asks for r > 0.3. We check absolute value or just positive? 
    # Usually "exceeds threshold" implies magnitude or positive direction depending on context.
    # Given "r > 0.3", we strictly follow positive threshold unless specified otherwise.
    # However, in neuroscience, negative correlations are also significant. 
    # The task says "r > 0.3", so we implement exactly that.
    significant = results_df[results_df['r'] > threshold]
    
    count = len(significant)
    logger.log("log_significant_correlations", count=count, threshold=threshold)

    if count > 0:
        for _, row in significant.iterrows():
            logger.log(
                "high_correlation_detected",
                metric=row['metric'],
                r=row['r'],
                p=row['p'],
                q=row['q'] if 'q' in row else None,
                significant=row['significant'] if 'significant' in row else None
            )
    else:
        logger.log("no_correlations_above_threshold", threshold=threshold)

def save_correlation_results(results_df: pd.DataFrame, output_path: Union[str, Path]) -> None:
    """
    Save the correlation results (including FDR corrected values) to a CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.log("save_correlation_results", path=str(output_path), rows=len(results_df))

def generate_full_metrics(metrics_df: pd.DataFrame, pca_scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge individual metric columns with PCA factor scores into a single DataFrame.
    """
    logger.log("generate_full_metrics")
    # Assuming both have 'subject_id'
    merged = pd.merge(metrics_df, pca_scores_df, on='subject_id', how='inner')
    logger.log("generate_full_metrics_success", rows=len(merged))
    return merged

def save_full_metrics(df: pd.DataFrame, output_path: Union[str, Path]) -> None:
    """
    Save the full metrics DataFrame to CSV.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.log("save_full_metrics", path=str(output_path), rows=len(df))

def main() -> None:
    """
    Main entry point for the correlation analysis pipeline.
    Orchestrates loading, PCA, correlation, FDR, and logging.
    """
    logger.log("main_start")
    
    try:
        # 1. Load Data
        metrics_path = Path("data/processed/aggregated_metrics.csv")
        if not metrics_path.exists():
            logger.log("main_error", reason="missing_aggregated_metrics")
            # Fallback to checking if we need to generate it? 
            # For T027, we assume the data exists or the pipeline failed earlier.
            raise FileNotFoundError(f"Required input file not found: {metrics_path}")
        
        df = load_metrics_data(metrics_path)
        
        # Define metric columns (adjust based on actual data schema if needed)
        metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
        # Filter to existing columns
        metric_cols = [c for c in metric_cols if c in df.columns]
        
        if not metric_cols:
            logger.log("main_error", reason="no_metric_columns_found")
            return

        # 2. PCA
        pca_path_loadings = Path("data/analysis/pca_loadings.csv")
        pca_path_scores = Path("data/analysis/factor_scores.csv")
        
        # Check if PCA already done? Or always run?
        # For simplicity, run it.
        if not pca_path_scores.exists():
            pca_model, pca_result = perform_pca_on_metrics(df, metric_cols)
            save_pca_results(pca_model, pca_result, pca_path_loadings, pca_path_scores)
            # Update df with scores for merging
            # The pca_result contains the scores.
            # We need to merge this back to the main df.
            # Let's assume pca_result has subject_id and pca factors.
            # We'll just use the scores file for the next step.
            scores_df = pd.read_csv(pca_path_scores)
            full_df = generate_full_metrics(df, scores_df)
            save_full_metrics(full_df, Path("data/analysis/full_metrics.csv"))
        else:
            # Load existing
            scores_df = pd.read_csv(pca_path_scores)
            full_df = generate_full_metrics(df, scores_df)
            save_full_metrics(full_df, Path("data/analysis/full_metrics.csv"))

        # 3. Correlations
        corr_results = run_correlations_with_fd_covariate(full_df, metric_cols)
        
        # 4. FDR
        corr_results = apply_fdr_correction(corr_results)
        
        # 5. Save Results
        save_correlation_results(corr_results, "data/analysis/correlations.csv")
        
        # 6. Log Significant Correlations (T027)
        log_significant_correlations(corr_results, CORRELATION_THRESHOLD)
        
        logger.log("main_success")
        
    except Exception as e:
        logger.log("main_error", reason=str(e))
        raise

if __name__ == "__main__":
    main()