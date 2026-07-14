"""
Correlation analysis module for US2.
Implements metric extraction, PCA, correlations with FD covariate, and FDR correction.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from code.logging_config import get_logger

logger = get_logger(__name__)

# Constants
ANALYSIS_DIR = Path("data/analysis")
PROCESSED_DIR = Path("data/processed")

# Ensure directories exist
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_metrics_data() -> pd.DataFrame:
    """
    Load aggregated metrics from the processed data directory.
    Expected file: data/processed/aggregated_metrics.csv
    """
    input_path = PROCESSED_DIR / "aggregated_metrics.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Run metric extraction (T021/T022) first."
        )
    df = pd.read_csv(input_path)
    logger.log("load_metrics_data", file=str(input_path), rows=len(df))
    return df


def run_correlations_with_fd_covariate(
    df: pd.DataFrame,
    metric_cols: List[str],
    target_col: str = "motor_score",
    covariate_col: str = "fd"
) -> pd.DataFrame:
    """
    Run Spearman/Pearson correlations between metrics and target, controlling for FD.
    
    This function performs partial correlation to control for the Framewise Displacement (FD) covariate.
    It calculates the correlation between each metric and the target score,
    removing the linear effect of FD from both variables first.
    
    Args:
        df: DataFrame containing metrics, target, and covariate.
        metric_cols: List of column names representing network metrics.
        target_col: Column name for the behavioral target (motor_score).
        covariate_col: Column name for the covariate (fd).
        
    Returns:
        DataFrame with columns: metric_name, r, p, n, covariate_controlled
    """
    if not all(col in df.columns for col in metric_cols + [target_col, covariate_col]):
        missing = set(metric_cols + [target_col, covariate_col]) - set(df.columns)
        raise ValueError(f"Missing required columns in input data: {missing}")

    results = []
    n = len(df)

    # Extract target and covariate
    y = df[target_col].values
    x_cov = df[covariate_col].values

    for metric in metric_cols:
        x = df[metric].values

        # Partial correlation calculation:
        # 1. Regress y on x_cov -> get residuals (y_resid)
        # 2. Regress x on x_cov -> get residuals (x_resid)
        # 3. Correlate x_resid and y_resid

        # Linear regression: y = b0 + b1 * x_cov + e_y
        # Using simple least squares for residuals
        # b1 = sum((x_cov - mean_x)(y - mean_y)) / sum((x_cov - mean_x)^2)
        mean_x_cov = np.mean(x_cov)
        mean_y = np.mean(y)
        mean_x = np.mean(x)

        num_y = np.sum((x_cov - mean_x_cov) * (y - mean_y))
        denom_y = np.sum((x_cov - mean_x_cov) ** 2)
        if denom_y == 0:
            # No variance in covariate, skip partialing
            y_resid = y - mean_y
        else:
            b1_y = num_y / denom_y
            y_resid = y - (mean_y + b1_y * (x_cov - mean_x_cov))

        # Linear regression: x = a0 + a1 * x_cov + e_x
        num_x = np.sum((x_cov - mean_x_cov) * (x - mean_x))
        denom_x = np.sum((x_cov - mean_x_cov) ** 2)
        if denom_x == 0:
            x_resid = x - mean_x
        else:
            b1_x = num_x / denom_x
            x_resid = x - (mean_x + b1_x * (x_cov - mean_x_cov))

        # Calculate correlation on residuals
        r, p_value = stats.pearsonr(x_resid, y_resid)

        results.append({
            "metric_name": metric,
            "r": r,
            "p": p_value,
            "n": n,
            "covariate_controlled": True
        })

    results_df = pd.DataFrame(results)
    logger.log("run_correlations_with_fd_covariate", 
               metrics=len(metric_cols), 
               target=target_col, 
               covariate=covariate_col,
               rows=len(results_df))
    return results_df


def apply_fdr_correction(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to the p-values in the results DataFrame.
    
    This implements the BH procedure to control the False Discovery Rate.
    It modifies the input DataFrame in-place and returns it with new columns:
    'q' (adjusted p-value) and 'significant' (boolean).
    
    Args:
        results_df: DataFrame containing a 'p' column with raw p-values.
        alpha: Significance threshold for FDR.
        
    Returns:
        DataFrame with added 'q' and 'significant' columns.
    """
    if "p" not in results_df.columns:
        raise ValueError("Input DataFrame must contain a 'p' column for FDR correction.")

    p_values = results_df["p"].values
    
    # Apply Benjamini-Hochberg procedure using statsmodels
    # method='fdr_bh' implements the Benjamini-Hochberg correction
    reject, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')

    results_df = results_df.copy()
    results_df["q"] = pvals_corrected
    results_df["significant"] = reject

    logger.log("apply_fdr_correction", 
               n_tests=len(p_values), 
               alpha=alpha, 
               significant_count=int(reject.sum()))
    
    return results_df


def save_correlation_results(results_df: pd.DataFrame, output_path: Optional[str] = None) -> Path:
    """
    Save correlation results to CSV.
    
    Args:
        results_df: DataFrame with correlation results (including q and significant).
        output_path: Optional path to save to. Defaults to data/analysis/correlations.csv.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = str(ANALYSIS_DIR / "correlations.csv")
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.log("save_correlation_results", path=str(output_path), rows=len(results_df))
    return output_path_obj


def run_pca_on_metrics(df: pd.DataFrame, 
                       metric_cols: List[str], 
                       n_components: int = 2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform PCA on network metrics.
    
    Args:
        df: DataFrame containing metrics.
        metric_cols: List of metric columns to include.
        n_components: Number of principal components to retain.
        
    Returns:
        Tuple of (loadings_df, scores_df).
        loadings_df: Columns are components, rows are original metrics.
        scores_df: Columns are components, rows are subjects (indexed by subject_id).
    """
    from sklearn.decomposition import PCA

    if not all(col in df.columns for col in metric_cols):
        missing = set(metric_cols) - set(df.columns)
        raise ValueError(f"Missing metric columns for PCA: {missing}")

    X = df[metric_cols].dropna()
    if len(X) == 0:
        raise ValueError("No valid data rows for PCA after dropping NaNs.")

    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(X)
    loadings = pca.components_.T

    # Create DataFrames
    loadings_df = pd.DataFrame(
        loadings, 
        index=metric_cols, 
        columns=[f"component_{i+1}" for i in range(n_components)]
    )
    
    scores_df = pd.DataFrame(
        scores, 
        index=X.index, 
        columns=[f"pca_factor_{i+1}" for i in range(n_components)]
    )
    scores_df.index.name = "subject_id"

    logger.log("run_pca_on_metrics", 
               n_components=n_components, 
               n_samples=len(X), 
               explained_variance_ratio=list(pca.explained_variance_ratio_))
    
    return loadings_df, scores_df


def generate_full_metrics(df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge individual metric columns with PCA factor scores into a single output DataFrame.
    
    Args:
        df: Original metrics DataFrame.
        scores_df: PCA scores DataFrame.
        
    Returns:
        Merged DataFrame containing all raw metrics and PCA factors.
    """
    # Reset index of scores_df to merge if index is subject_id
    scores_reset = scores_df.reset_index()
    if "subject_id" not in scores_reset.columns:
        # Try to infer subject_id column if not named exactly
        if len(df) == len(scores_reset) and "subject_id" in df.columns:
            scores_reset["subject_id"] = df["subject_id"].values
        else:
            raise ValueError("Cannot merge: subject_id alignment failed.")

    merged = pd.merge(df, scores_reset, on="subject_id", how="inner")
    logger.log("generate_full_metrics", 
               input_rows=len(df), 
               scores_rows=len(scores_reset), 
               output_rows=len(merged))
    return merged


def main():
    """
    Main entry point for the correlation analysis pipeline.
    Executes:
    1. Load metrics
    2. Run correlations with FD covariate
    3. Apply FDR correction
    4. Run PCA
    5. Generate full metrics
    6. Save all outputs
    """
    logger.log("main", step="start")
    
    # 1. Load data
    try:
        df = load_metrics_data()
    except FileNotFoundError as e:
        logger.log("main", step="fail_load", error=str(e))
        raise

    # Define metrics to analyze (based on T021/T022 output)
    metric_cols = ["modularity", "global_efficiency", "participation_coef", "within_module_degree"]
    
    # Filter to rows that have all required metrics
    valid_cols = [c for c in metric_cols if c in df.columns]
    if len(valid_cols) < len(metric_cols):
        logger.log("main", warning="Some metrics missing, using subset", missing=list(set(metric_cols)-set(valid_cols)))
    
    if "motor_score" not in df.columns:
        raise ValueError("Target column 'motor_score' not found in data.")
    if "fd" not in df.columns:
        raise ValueError("Covariate column 'fd' not found in data.")

    # 2. Run correlations
    corr_results = run_correlations_with_fd_covariate(df, valid_cols)
    
    # 3. Apply FDR correction (T025)
    corr_results = apply_fdr_correction(corr_results)
    
    # Save correlation results
    save_correlation_results(corr_results)
    logger.log("main", step="saved_correlations")

    # 4. Run PCA
    # Ensure we have enough samples for PCA
    if len(df) > 2:
        loadings, scores = run_pca_on_metrics(df, valid_cols)
        
        # Save PCA outputs
        loadings_path = ANALYSIS_DIR / "pca_loadings.csv"
        scores_path = ANALYSIS_DIR / "factor_scores.csv"
        loadings.to_csv(loadings_path)
        scores.to_csv(scores_path)
        logger.log("main", step="saved_pca", loadings_file=str(loadings_path), scores_file=str(scores_path))

        # 5. Generate full metrics
        full_metrics = generate_full_metrics(df, scores)
        full_metrics_path = ANALYSIS_DIR / "full_metrics.csv"
        full_metrics.to_csv(full_metrics_path, index=False)
        logger.log("main", step="saved_full_metrics", file=str(full_metrics_path))
    else:
        logger.log("main", step="skipped_pca", reason="Insufficient samples")

    logger.log("main", step="complete")
    return corr_results


if __name__ == "__main__":
    main()