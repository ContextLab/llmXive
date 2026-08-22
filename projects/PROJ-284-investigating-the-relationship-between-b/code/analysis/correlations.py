"""
Correlation analysis module for brain network metrics and sensorimotor performance.
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
FDR_ALPHA = 0.05
CORRELATION_THRESHOLD = 0.3

def load_metrics_data(filepath: str = "data/analysis/aggregated_metrics.csv") -> pd.DataFrame:
    """Load aggregated metrics data for analysis."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    return pd.read_csv(filepath)

def run_pca_on_metrics(df: pd.DataFrame, n_components: int = 2) -> Tuple[PCA, pd.DataFrame, pd.DataFrame]:
    """
    Perform PCA on network metrics.
    Returns: (pca_model, loadings_df, scores_df)
    """
    # Select numeric columns for PCA
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude subject_id if present
    if 'subject_id' in numeric_cols:
        numeric_cols.remove('subject_id')

    if len(numeric_cols) < 2:
        raise ValueError("Not enough numeric columns for PCA")

    X = df[numeric_cols].values
    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(X)

    # Create loadings dataframe
    loadings = pd.DataFrame(
        pca.components_.T,
        columns=[f'PC{i+1}' for i in range(n_components)],
        index=numeric_cols
    )

    # Create scores dataframe
    scores_df = pd.DataFrame(scores, columns=[f'PC{i+1}' for i in range(n_components)])
    if 'subject_id' in df.columns:
        scores_df.insert(0, 'subject_id', df['subject_id'].values)

    return pca, loadings, scores_df

def save_pca_outputs(loadings: pd.DataFrame, scores: pd.DataFrame, output_dir: str = "data/analysis"):
    """Save PCA results to CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    loadings.to_csv(output_path / "pca_loadings.csv", index=True)
    scores.to_csv(output_path / "factor_scores.csv", index=False)
    logger.log("pca_outputs_saved", {"loadings_file": "pca_loadings.csv", "scores_file": "factor_scores.csv"})

def generate_full_metrics(aggregated_df: pd.DataFrame, pca_scores: pd.DataFrame) -> pd.DataFrame:
    """
    Merge aggregated metrics with PCA factor scores.
    """
    # Ensure subject_id is in both
    if 'subject_id' not in aggregated_df.columns or 'subject_id' not in pca_scores.columns:
        raise ValueError("Both DataFrames must contain 'subject_id'")

    full_df = pd.merge(aggregated_df, pca_scores, on='subject_id', how='inner')
    return full_df

def save_full_metrics(full_df: pd.DataFrame, output_path: str = "data/analysis/full_metrics.csv"):
    """Save full metrics dataframe to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    full_df.to_csv(output_path, index=False)
    logger.log("full_metrics_saved", {"path": output_path, "rows": len(full_df)})

def run_simple_correlations(df: pd.DataFrame, metric_col: str, target_col: str = 'motor_score') -> Dict[str, float]:
    """
    Run simple Pearson correlation between a metric and motor score.
    Returns dict with r, p_value.
    """
    x = df[metric_col].dropna()
    y = df[target_col].loc[x.index].dropna()

    if len(x) < 3:
        return {'r': np.nan, 'p_value': np.nan, 'n': len(x)}

    r, p = stats.pearsonr(x, y)
    return {'r': r, 'p_value': p, 'n': len(x)}

def run_correlations_with_fd_covariate(df: pd.DataFrame, metric_col: str, target_col: str = 'motor_score', covariate_col: str = 'fd') -> Dict[str, float]:
    """
    Run partial correlation controlling for FD.
    Uses statsmodels for partial correlation.
    """
    from statsmodels.stats.correlation_tools import corr_nearest

    x = df[metric_col].dropna()
    y = df[target_col].loc[x.index].dropna()
    z = df[covariate_col].loc[x.index].dropna()

    # Align all series
    common_idx = x.index.intersection(y.index).intersection(z.index)
    x = x.loc[common_idx]
    y = y.loc[common_idx]
    z = z.loc[common_idx]

    if len(x) < 4:
        return {'r': np.nan, 'p_value': np.nan, 'n': len(x), 'partial_r': np.nan}

    # Calculate partial correlation manually
    # r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1 - r_xz^2) * (1 - r_yz^2))
    r_xy, p_xy = stats.pearsonr(x, y)
    r_xz, p_xz = stats.pearsonr(x, z)
    r_yz, p_yz = stats.pearsonr(y, z)

    numerator = r_xy - (r_xz * r_yz)
    denominator_sq = (1 - r_xz**2) * (1 - r_yz**2)

    if denominator_sq <= 0:
        return {'r': r_xy, 'p_value': p_xy, 'n': len(x), 'partial_r': np.nan}

    partial_r = numerator / np.sqrt(denominator_sq)

    # Convert partial r to p-value using t-distribution
    # t = r * sqrt((n-2) / (1-r^2))
    n = len(x)
    if abs(partial_r) >= 1.0:
        p_partial = 0.0
    else:
        t_stat = partial_r * np.sqrt((n - 2) / (1 - partial_r**2))
        p_partial = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))

    return {'r': r_xy, 'p_value': p_xy, 'n': n, 'partial_r': partial_r, 'partial_p': p_partial}

def apply_fdr_correction(results_df: pd.DataFrame, p_col: str = 'p_value', alpha: float = FDR_ALPHA) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to a set of p-values.
    Merges all p-values into a single set, sorts, calculates q-values, and outputs results.
    """
    if p_col not in results_df.columns:
        raise ValueError(f"Column '{p_col}' not found in results DataFrame")

    # Create a copy to avoid modifying original
    df = results_df.copy()
    df = df.dropna(subset=[p_col])

    if len(df) == 0:
        logger.log("fdr_correction_skipped", {"reason": "no_valid_p_values"})
        return df

    # Sort by p-value
    df = df.sort_values(by=p_col)

    n = len(df)
    # BH procedure: q_i = p_i * n / i
    # Where i is the rank (1-indexed)
    ranks = np.arange(1, n + 1)
    df['rank'] = ranks
    df['q_value'] = (df[p_col] * n) / ranks

    # Ensure monotonicity: q_i <= q_{i+1} (cumulative min from bottom up)
    # We must ensure that q-values are non-decreasing with rank
    # Actually, BH ensures q_i <= q_{i+1} is NOT guaranteed by simple formula,
    # so we do cumulative minimum from the largest rank down to smallest
    df['q_value'] = df['q_value'].cummax() # Wait, standard BH is cumulative min from bottom?
    # Correct BH: q_i = min(p_j * n / j for j >= i)
    # So we calculate from bottom (largest p) up to top (smallest p)
    df['q_value'] = df['q_value'].iloc[::-1].cummin().iloc[::-1]

    # Cap at 1.0
    df['q_value'] = df['q_value'].clip(upper=1.0)

    # Determine significance
    df['significant'] = df['q_value'] < alpha

    # Sort back to original order (or keep sorted by p-value? Usually keep sorted by p for reporting)
    # We'll keep sorted by p-value for the output file as it's standard for FDR tables
    return df

def save_correlations_to_csv(results_df: pd.DataFrame, output_path: str = "data/analysis/correlation_results.csv"):
    """Save correlation results to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.log("correlations_saved", {"path": output_path, "rows": len(results_df)})

def log_significant_correlations(results_df: pd.DataFrame, threshold: float = CORRELATION_THRESHOLD, fdr_alpha: float = FDR_ALPHA):
    """Log significant correlations to the logger."""
    sig_rows = results_df[
        (results_df['significant']) &
        (results_df['q_value'] < fdr_alpha) &
        (abs(results_df.get('partial_r', results_df['r'])) > threshold)
    ]

    if len(sig_rows) > 0:
        for _, row in sig_rows.iterrows():
            metric = row.get('metric_name', 'unknown')
            r_val = row.get('partial_r', row['r'])
            q_val = row['q_value']
            logger.log(
                "significant_correlation_found",
                {"metric": metric, "r": r_val, "q": q_val}
            )
    else:
        logger.log("no_significant_correlations", {"threshold": threshold, "fdr_alpha": fdr_alpha})

def process_metrics_with_batching(df: pd.DataFrame, batch_size: int = 50) -> pd.DataFrame:
    """Process correlations in batches to manage memory."""
    results = []
    metrics = [col for col in df.columns if col not in ['subject_id', 'motor_score', 'fd']]

    for i in range(0, len(metrics), batch_size):
        batch = metrics[i:i+batch_size]
        for metric in batch:
            try:
                res = run_correlations_with_fd_covariate(df, metric)
                res['metric_name'] = metric
                results.append(res)
            except Exception as e:
                logger.log("correlation_failed", {"metric": metric, "error": str(e)})

    return pd.DataFrame(results)

def main():
    """
    Main entry point for correlation analysis.
    1. Load aggregated metrics.
    2. Run PCA.
    3. Save PCA outputs.
    4. Generate full metrics.
    5. Run correlations.
    6. Apply FDR correction.
    7. Save FDR corrected results.
    """
    # Paths
    agg_path = "data/analysis/aggregated_metrics.csv"
    pca_load_path = "data/analysis/pca_loadings.csv"
    pca_scores_path = "data/analysis/factor_scores.csv"
    full_metrics_path = "data/analysis/full_metrics.csv"
    corr_results_path = "data/analysis/correlation_results.csv"
    fdr_output_path = "data/analysis/fdr_corrected_results.csv"

    # 1. Load data
    logger.log("analysis_start", {"input": agg_path})
    if not Path(agg_path).exists():
        raise FileNotFoundError(f"Required input file missing: {agg_path}")

    df_agg = load_metrics_data(agg_path)
    logger.log("data_loaded", {"rows": len(df_agg)})

    # 2. Run PCA
    logger.log("pca_start", {"n_components": 2})
    pca_model, loadings, scores = run_pca_on_metrics(df_agg, n_components=2)
    save_pca_outputs(loadings, scores)
    logger.log("pca_complete", {"loadings_file": pca_load_path, "scores_file": pca_scores_path})

    # 3. Generate full metrics
    df_full = generate_full_metrics(df_agg, scores)
    save_full_metrics(df_full, full_metrics_path)
    logger.log("full_metrics_generated", {"path": full_metrics_path})

    # 4. Run correlations
    # We need to run correlations on the full metrics dataframe
    # Columns to correlate: original metrics + PCA factors
    cols_to_test = [c for c in df_full.columns if c not in ['subject_id', 'motor_score', 'fd']]

    logger.log("correlation_start", {"metrics": len(cols_to_test)})
    corr_results = []

    for metric in cols_to_test:
        try:
            res = run_correlations_with_fd_covariate(df_full, metric)
            res['metric_name'] = metric
            corr_results.append(res)
        except Exception as e:
            logger.log("correlation_error", {"metric": metric, "error": str(e)})
            continue

    df_corr = pd.DataFrame(corr_results)
    save_correlations_to_csv(df_corr, corr_results_path)
    logger.log("correlations_complete", {"path": corr_results_path, "rows": len(df_corr)})

    # 5. Apply FDR correction
    # Merge all p-values (from individual metrics and PCA factors) into a single set
    # The df_corr already contains all results
    logger.log("fdr_start", {"alpha": FDR_ALPHA})
    df_fdr = apply_fdr_correction(df_corr, p_col='partial_p', alpha=FDR_ALPHA)
    # If partial_p is missing (nan), fall back to p_value?
    # The apply_fdr_correction drops NaNs. If we need to keep rows with NaN partial_p,
    # we should handle that. For now, we assume valid p-values exist.
    # If partial_p is NaN, we might want to use p_value.
    # Let's ensure we have a p-value column for FDR.
    # If partial_p is NaN, use p_value.
    if 'partial_p' in df_fdr.columns and df_fdr['partial_p'].isna().all():
         # Fallback if partial correlation failed for all
         df_fdr = apply_fdr_correction(df_corr, p_col='p_value', alpha=FDR_ALPHA)

    # Save FDR results
    df_fdr.to_csv(fdr_output_path, index=False)
    logger.log("fdr_complete", {"path": fdr_output_path, "rows": len(df_fdr)})

    # 6. Log significant findings
    log_significant_correlations(df_fdr)

    logger.log("analysis_complete")
    return df_fdr

if __name__ == "__main__":
    main()