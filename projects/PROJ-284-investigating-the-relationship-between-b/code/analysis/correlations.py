"""
Correlation analysis module for US2.
Implements metric extraction, PCA, correlation with covariates, FDR correction, and threshold logging.
"""
from __future__ import annotations

import os
import sys
import gc
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats

from code.logging_config import get_logger, log_operation
from code.models import CorrelationResult

# Configuration
CORRELATION_THRESHOLD = 0.3
FDR_ALPHA = 0.05
MEMORY_LIMIT_GB = 7.0

logger = get_logger(__name__)


def load_metrics_data_safe(file_path: str) -> Optional[pd.DataFrame]:
    """Safely load metrics data, handling missing files gracefully."""
    path = Path(file_path)
    if not path.exists():
        logger.warning("Metrics file not found", path=str(path))
        return None
    try:
        df = pd.read_csv(path)
        logger.log("metrics_loaded", rows=len(df), columns=list(df.columns))
        return df
    except Exception as e:
        logger.error("Failed to load metrics", error=str(e), path=str(path))
        return None


def compute_correlation_with_covariate(
    x: np.ndarray,
    y: np.ndarray,
    covariate: Optional[np.ndarray] = None
) -> Tuple[float, float]:
    """
    Compute correlation between x and y, optionally partialling out a covariate.
    Returns (r, p_value).
    """
    if covariate is not None:
        # Partial correlation
        # Residualize x and y against covariate
        _, _, x_resid, y_resid = stats.linregress(x, covariate), stats.linregress(y, covariate), None, None
        
        # Manual partial correlation calculation
        # 1. Regress x on covariate -> get residuals
        # 2. Regress y on covariate -> get residuals
        # 3. Correlate residuals
        
        # Fit model: x = beta0 + beta1*covariate + e_x
        X = np.column_stack([np.ones(len(covariate)), covariate])
        try:
            beta_x = np.linalg.lstsq(X, x, rcond=None)[0]
            x_resid = x - X @ beta_x
            
            beta_y = np.linalg.lstsq(X, y, rcond=None)[0]
            y_resid = y - X @ beta_y
            
            # Correlate residuals
            r, p = stats.pearsonr(x_resid, y_resid)
        except np.linalg.LinAlgError:
            logger.warning("Singular matrix in partial correlation, using standard correlation")
            r, p = stats.pearsonr(x, y)
    else:
        r, p = stats.pearsonr(x, y)
    
    return float(r), float(p)


def apply_fdr_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction.
    Returns list of adjusted p-values (q-values).
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # BH procedure
    q_values = np.zeros(n)
    for i, p in enumerate(sorted_p):
        rank = i + 1
        q_values[sorted_indices[i]] = min(p * n / rank, 1.0)
    
    # Ensure monotonicity (cumulative min from largest to smallest)
    for i in range(n - 2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i + 1])
    
    return q_values.tolist()


def run_correlation_analysis(
    metrics_df: pd.DataFrame,
    target_col: str,
    covariate_col: Optional[str] = None
) -> List[CorrelationResult]:
    """
    Run correlation analysis for each metric against target.
    Logs high correlations (|r| > CORRELATION_THRESHOLD).
    """
    results = []
    
    # Filter out non-numeric columns
    numeric_cols = metrics_df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col not in numeric_cols:
        logger.error("Target column not numeric", target=target_col)
        return results
    
    target = metrics_df[target_col].dropna().values
    valid_indices = metrics_df[target_col].notna()
    
    if covariate_col and covariate_col in metrics_df.columns:
        covariate = metrics_df.loc[valid_indices, covariate_col].values
    else:
        covariate = None
    
    for col in numeric_cols:
        if col == target_col:
            continue
        
        x = metrics_df.loc[valid_indices, col].values
        if len(x) != len(target):
            continue
        
        r, p = compute_correlation_with_covariate(x, target, covariate)
        
        # LOGGING FOR HIGH CORRELATIONS (T027)
        if abs(r) > CORRELATION_THRESHOLD:
            logger.log(
                "high_correlation_detected",
                metric=col,
                target=target_col,
                r=r,
                p=p,
                threshold=CORRELATION_THRESHOLD,
                direction="positive" if r > 0 else "negative"
            )
        
        # Calculate FDR later, store raw values first
        results.append(CorrelationResult(
            metric_name=col,
            r=r,
            p=p,
            q=None,  # Will be filled later
            significant=False,
            covariate_controlled=covariate is not None
        ))
    
    return results


def compute_and_save_pca(
    metrics_df: pd.DataFrame,
    output_dir: str = "data/analysis"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform PCA on network metrics.
    Returns (loadings_df, scores_df).
    """
    from sklearn.decomposition import PCA
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Select numeric metric columns (exclude subject_id if present)
    metric_cols = [c for c in metrics_df.columns if c != 'subject_id' and metrics_df[c].dtype in [np.float64, np.float32, np.int64, np.int32]]
    
    if len(metric_cols) < 2:
        logger.warning("Not enough columns for PCA", columns=metric_cols)
        # Return empty DataFrames with correct schema
        loadings_df = pd.DataFrame(columns=["component_1", "component_2"])
        scores_df = pd.DataFrame(columns=["subject_id", "pca_factor_1"])
        return loadings_df, scores_df
    
    data = metrics_df[metric_cols].dropna()
    if data.empty:
        logger.warning("No valid data for PCA")
        return pd.DataFrame(), pd.DataFrame()
    
    pca = PCA(n_components=min(2, len(metric_cols)))
    scores = pca.fit_transform(data)
    
    # Create scores DataFrame
    scores_df = pd.DataFrame(scores, columns=[f'pca_factor_{i+1}' for i in range(scores.shape[1])])
    scores_df.insert(0, 'subject_id', metrics_df.loc[data.index, 'subject_id'].values)
    
    # Create loadings DataFrame
    loadings = pd.DataFrame(pca.components_.T, columns=[f'component_{i+1}' for i in range(pca.n_components_)])
    loadings.insert(0, 'metric', metric_cols)
    
    # Save to disk
    loadings.to_csv(output_path / "pca_loadings.csv", index=False)
    scores_df.to_csv(output_path / "factor_scores.csv", index=False)
    
    logger.log("pca_completed", n_components=pca.n_components_, variance_explained=list(pca.explained_variance_ratio_))
    
    return loadings, scores_df


def merge_metrics_and_pca_scores(
    metrics_df: pd.DataFrame,
    scores_df: pd.DataFrame
) -> pd.DataFrame:
    """Merge raw metrics with PCA factor scores."""
    merged = pd.merge(metrics_df, scores_df, on='subject_id', how='left')
    logger.log("metrics_merged", rows=len(merged), columns=list(merged.columns))
    return merged


def save_full_metrics(merged_df: pd.DataFrame, output_path: str) -> None:
    """Save the full metrics DataFrame to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    logger.log("full_metrics_saved", path=output_path, rows=len(merged_df))


def main() -> None:
    """Main entry point for correlation analysis pipeline."""
    logger.log("analysis_started")
    
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    metrics_path = base_dir / "data" / "processed" / "aggregated_metrics.csv"
    output_dir = base_dir / "data" / "analysis"
    
    if not metrics_path.exists():
        logger.error("Aggregated metrics file not found", path=str(metrics_path))
        sys.exit(1)
    
    # Load data
    df = load_metrics_data_safe(str(metrics_path))
    if df is None:
        sys.exit(1)
    
    # 1. PCA
    logger.log("starting_pca")
    loadings, scores = compute_and_save_pca(df, str(output_dir))
    
    # 2. Merge
    merged = merge_metrics_and_pca_scores(df, scores)
    save_full_metrics(merged, str(output_dir / "full_metrics.csv"))
    
    # 3. Correlations
    logger.log("starting_correlations")
    # Assuming 'motor_score' is the target, fallback to first available numeric if missing
    target_col = 'motor_score' if 'motor_score' in df.columns else df.select_dtypes(include=[np.number]).columns[0]
    covariate_col = 'fd' if 'fd' in df.columns else None
    
    results = run_correlation_analysis(df, target_col, covariate_col)
    
    # 4. FDR Correction
    p_values = [r.p for r in results]
    q_values = apply_fdr_correction(p_values)
    
    for res, q in zip(results, q_values):
        res.q = q
        res.significant = q < FDR_ALPHA
    
    # Log significant results
    sig_count = sum(1 for r in results if r.significant)
    logger.log("correlation_analysis_complete", total=len(results), significant=sig_count)
    
    # Save correlation results (optional, for reporting)
    corr_df = pd.DataFrame([
        {
            'metric': r.metric_name,
            'r': r.r,
            'p': r.p,
            'q': r.q,
            'significant': r.significant
        }
        for r in results
    ])
    corr_df.to_csv(output_dir / "correlation_results.csv", index=False)
    
    logger.log("analysis_finished")


if __name__ == "__main__":
    main()