"""
Analysis module for correlation between network metrics and sensorimotor performance.
Implements PCA, partial correlations with FD covariate, FDR correction, and threshold logging.
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

# Configuration constants
FDR_ALPHA = 0.05
CORRELATION_THRESHOLD = 0.3
DATA_DIR = Path("data/analysis")
FULL_METRICS_PATH = DATA_DIR / "full_metrics.csv"
PCA_LOADINGS_PATH = DATA_DIR / "pca_loadings.csv"
FACTOR_SCORES_PATH = DATA_DIR / "factor_scores.csv"

def load_metrics_data() -> pd.DataFrame:
    """
    Load the full metrics dataset containing individual metrics and PCA scores.
    Returns:
        DataFrame with columns: subject_id, modularity, global_efficiency,
        participation_coef, within_module_degree, pca_factor_1, ...
    """
    if not FULL_METRICS_PATH.exists():
        raise FileNotFoundError(f"Full metrics file not found at {FULL_METRICS_PATH}. "
                                "Run metric extraction and PCA steps first.")
    df = pd.read_csv(FULL_METRICS_PATH)
    logger.log("load_metrics_data", file=str(FULL_METRICS_PATH), rows=len(df))
    return df

def run_pca(df: pd.DataFrame, metric_cols: Optional[List[str]] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run PCA on network metrics.
    Args:
        df: DataFrame with metric columns.
        metric_cols: List of columns to use for PCA. Defaults to standard metrics.
    Returns:
        Tuple of (loadings_df, scores_df)
    """
    if metric_cols is None:
        metric_cols = ["modularity", "global_efficiency", "participation_coef", "within_module_degree"]

    # Ensure columns exist
    available_cols = [c for c in metric_cols if c in df.columns]
    if len(available_cols) < 2:
        raise ValueError(f"Need at least 2 metric columns for PCA, found: {available_cols}")

    data_matrix = df[available_cols].dropna()
    if data_matrix.empty:
        raise ValueError("No valid data rows for PCA after dropping NaNs.")

    # Standardize
    mean_vals = data_matrix.mean()
    std_vals = data_matrix.std()
    std_vals[std_vals == 0] = 1  # Avoid div by zero
    standardized = (data_matrix - mean_vals) / std_vals

    # Compute covariance matrix
    cov_matrix = standardized.cov()

    # Eigen decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    # Sort descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Loadings: eigenvectors * sqrt(eigenvalues)
    loadings = pd.DataFrame(
        eigenvectors * np.sqrt(eigenvalues),
        columns=[f"component_{i+1}" for i in range(len(eigenvalues))],
        index=available_cols
    )

    # Factor scores: standardized data * eigenvectors
    scores_matrix = standardized.values @ eigenvectors
    scores_df = pd.DataFrame(
        scores_matrix,
        columns=[f"pca_factor_{i+1}" for i in range(scores_matrix.shape[1])],
        index=data_matrix.index
    )
    scores_df["subject_id"] = df.loc[data_matrix.index, "subject_id"].values

    logger.log("run_pca", n_components=len(eigenvalues), variance_explained=eigenvalues.sum())
    return loadings, scores_df

def compute_and_save_pca(df: pd.DataFrame) -> None:
    """
    Compute PCA and save loadings and scores to CSV files.
    """
    loadings, scores = run_pca(df)
    
    # Save loadings
    loadings.to_csv(PCA_LOADINGS_PATH)
    logger.log("compute_and_save_pca", output=str(PCA_LOADINGS_PATH))
    
    # Save scores (reordered with subject_id first)
    cols = ["subject_id"] + [c for c in scores.columns if c != "subject_id"]
    scores[cols].to_csv(FACTOR_SCORES_PATH)
    logger.log("compute_and_save_pca", output=str(FACTOR_SCORES_PATH))

def partial_correlation(
    x: np.ndarray, 
    y: np.ndarray, 
    z: np.ndarray
) -> Tuple[float, float]:
    """
    Compute partial correlation between x and y, controlling for z.
    Args:
        x, y: 1D arrays of data.
        z: 1D array of covariate (FD).
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    # Residuals of x ~ z
    slope_xz, intercept_xz, r_xz, _, _ = stats.linregress(z, x)
    res_x = x - (slope_xz * z + intercept_xz)
    
    # Residuals of y ~ z
    slope_yz, intercept_yz, r_yz, _, _ = stats.linregress(z, y)
    res_y = y - (slope_yz * z + intercept_yz)
    
    # Correlation of residuals
    r, p = stats.pearsonr(res_x, res_y)
    return r, p

def run_metric_correlations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run correlations for each individual metric against motor_score, controlling for FD.
    Args:
        df: DataFrame with metric columns and 'motor_score', 'fd'.
    Returns:
        List of dicts with correlation results.
    """
    metric_cols = ["modularity", "global_efficiency", "participation_coef", "within_module_degree"]
    results = []
    
    # Ensure required columns exist
    required = metric_cols + ["motor_score", "fd"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    for col in metric_cols:
        x = df[col].values
        y = df["motor_score"].values
        z = df["fd"].values
        
        # Drop NaNs
        mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
        if mask.sum() < 3:
            logger.log("run_metric_correlations", warning=f"Not enough data for {col}")
            continue
            
        r, p = partial_correlation(x[mask], y[mask], z[mask])
        results.append({
            "metric_name": col,
            "r": r,
            "p": p,
            "n": mask.sum()
        })
        
    logger.log("run_metric_correlations", n_metrics=len(results))
    return results

def apply_fdr_correction(results: List[Dict[str, Any]], alpha: float = FDR_ALPHA) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    Args:
        results: List of dicts with 'p' values.
        alpha: Significance threshold.
    Returns:
        Updated list with 'q' (FDR adjusted p) and 'significant' flag.
    """
    n = len(results)
    if n == 0:
        return results
        
    # Sort by p-value
    sorted_indices = np.argsort([r["p"] for r in results])
    sorted_results = [results[i] for i in sorted_indices]
    
    # BH procedure
    for i, res in enumerate(sorted_results):
        rank = i + 1
        q = res["p"] * n / rank
        res["q"] = min(q, 1.0)  # Cap at 1.0
        res["significant"] = res["q"] <= alpha
        
    logger.log("apply_fdr_correction", alpha=alpha, n_significant=sum(r["significant"] for r in results))
    return results

def log_threshold_correlations(results: List[Dict[str, Any]], threshold: float = CORRELATION_THRESHOLD) -> None:
    """
    Log correlations where |r| > threshold.
    Args:
        results: List of correlation result dicts.
        threshold: Absolute correlation threshold (default 0.3).
    """
    logger.log("log_threshold_correlations", threshold=threshold, count=0)
    for res in results:
        if abs(res["r"]) > threshold:
            logger.log(
                "threshold_exceeded",
                metric=res["metric_name"],
                r=res["r"],
                p=res["p"],
                q=res.get("q", None),
                significant=res.get("significant", False)
            )
    logger.log("log_threshold_correlations", count=sum(1 for r in results if abs(r["r"]) > threshold))

def merge_metrics_and_pca(metrics_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge raw metrics with PCA factor scores.
    """
    # Ensure subject_id is in both
    if "subject_id" not in metrics_df.columns or "subject_id" not in scores_df.columns:
        raise ValueError("Both DataFrames must have 'subject_id' column")
        
    merged = pd.merge(metrics_df, scores_df, on="subject_id", how="inner")
    logger.log("merge_metrics_and_pca", rows=len(merged))
    return merged

def create_full_metrics_output() -> None:
    """
    Load metrics, run PCA, merge, and save full_metrics.csv.
    """
    # Load raw metrics (assuming they are in a specific format or derived from earlier steps)
    # For this implementation, we assume a raw metrics file exists or is generated
    # If not, we might need to load from a different source or generate synthetic for testing
    # However, per constraints, we must use real data. We'll assume the data exists.
    
    # In a real pipeline, this would load from data/processed or similar
    # Here we try to load from a hypothetical raw metrics file or fallback
    raw_metrics_path = Path("data/analysis/raw_metrics.csv")
    if not raw_metrics_path.exists():
        # Fallback: try to load from full_metrics if it exists (circular dependency check)
        if FULL_METRICS_PATH.exists():
            logger.log("create_full_metrics_output", warning="Using existing full_metrics as source")
            df = pd.read_csv(FULL_METRICS_PATH)
            # If it already has PCA, we might just need to save it
            if "pca_factor_1" in df.columns:
                df.to_csv(FULL_METRICS_PATH)
                return
        else:
            raise FileNotFoundError("No raw metrics found. Run metric extraction first.")
    else:
        df = pd.read_csv(raw_metrics_path)
        
    # Run PCA
    loadings, scores = run_pca(df)
    loadings.to_csv(PCA_LOADINGS_PATH)
    scores.to_csv(FACTOR_SCORES_PATH)
    
    # Merge
    if "subject_id" not in df.columns:
        df["subject_id"] = range(len(df))
        
    merged = merge_metrics_and_pca(df, scores)
    merged.to_csv(FULL_METRICS_PATH, index=False)
    logger.log("create_full_metrics_output", output=str(FULL_METRICS_PATH))

def main() -> None:
    """
    Main entry point for correlation analysis pipeline.
    """
    logger.log("main", step="start")
    
    # 1. Create full metrics (PCA + merge)
    if not FULL_METRICS_PATH.exists():
        create_full_metrics_output()
        
    # 2. Load data
    df = load_metrics_data()
    
    # 3. Run correlations
    results = run_metric_correlations(df)
    
    # 4. Apply FDR
    results = apply_fdr_correction(results)
    
    # 5. Log threshold correlations (T027)
    log_threshold_correlations(results)
    
    # 6. Save final results (optional, or handled by report generator)
    results_df = pd.DataFrame(results)
    results_df.to_csv(DATA_DIR / "correlation_results.csv", index=False)
    
    logger.log("main", step="complete", n_results=len(results))

if __name__ == "__main__":
    main()