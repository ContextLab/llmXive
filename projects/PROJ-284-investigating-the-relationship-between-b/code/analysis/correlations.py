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
from sklearn.decomposition import PCA

from code.logging_config import get_logger

logger = get_logger(__name__)

# Constants
CORRELATION_THRESHOLD = 0.3
FDR_ALPHA = 0.05

def load_metrics_data(file_path: str = "data/processed/aggregated_metrics.csv") -> pd.DataFrame:
    """Load aggregated metrics from disk."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    return pd.read_csv(path)

def apply_fdr_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    Returns adjusted p-values.
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # Calculate BH adjusted p-values
    adjusted = np.zeros(n)
    for i in range(n):
        # BH formula: p * n / rank
        rank = i + 1
        adjusted[sorted_indices[i]] = sorted_p[i] * n / rank

    # Ensure monotonicity (cumulative min from largest rank to smallest)
    for i in range(n - 2, -1, -1):
        adjusted[sorted_indices[i]] = min(adjusted[sorted_indices[i]], adjusted[sorted_indices[i+1]])

    # Clip to [0, 1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    return adjusted.tolist()

def run_correlations_with_fd_covariate(
    df: pd.DataFrame,
    metric_cols: List[str],
    target_col: str = "motor_score",
    fd_col: str = "MeanFD"
) -> pd.DataFrame:
    """
    Run Spearman/Pearson correlations between metrics and target,
    controlling for FD covariate using partial correlation.
    """
    results = []

    # Prepare data
    valid_cols = [c for c in [target_col, fd_col] + metric_cols if c in df.columns]
    clean_df = df[valid_cols].dropna()

    if len(clean_df) < 3:
        logger.log("correlation_insufficient_data", count=len(clean_df))
        return pd.DataFrame()

    for metric in metric_cols:
        if metric not in clean_df.columns:
            continue

        x = clean_df[metric].values
        y = clean_df[target_col].values
        z = clean_df[fd_col].values

        # Partial correlation: corr(x, y | z)
        # Using scipy.stats.pearsonr for partial correlation calculation
        try:
            r_xy, p_xy = stats.pearsonr(x, y)
            r_xz, p_xz = stats.pearsonr(x, z)
            r_yz, p_yz = stats.pearsonr(y, z)

            # Partial correlation formula
            denom = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
            if denom == 0:
                partial_r = 0.0
            else:
                partial_r = (r_xy - r_xz * r_yz) / denom

            # Convert to t-statistic for p-value
            n = len(x)
            df_stats = n - 3
            if df_stats <= 0:
                partial_p = 1.0
            else:
                t_stat = partial_r * np.sqrt(df_stats / (1 - partial_r**2 + 1e-10))
                partial_p = 2 * (1 - stats.t.cdf(abs(t_stat), df_stats))

            results.append({
                "metric": metric,
                "r": partial_r,
                "p_uncorrected": partial_p,
                "n": n
            })
        except Exception as e:
            logger.log("correlation_error", metric=metric, error=str(e))
            continue

    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df["q"] = apply_fdr_correction(result_df["p_uncorrected"].tolist())
        result_df["significant"] = result_df["q"] < FDR_ALPHA
    return result_df

def log_significant_correlations(results_df: pd.DataFrame) -> None:
    """
    Log correlations that exceed the threshold (r > 0.3) and are significant.
    Implements T027 requirement.
    """
    if results_df.empty:
        logger.log("no_correlation_results", count=0)
        return

    significant_high = results_df[
        (results_df["r"].abs() > CORRELATION_THRESHOLD) &
        (results_df["significant"] == True)
    ]

    if significant_high.empty:
        logger.log("no_significant_high_correlations", threshold=CORRELATION_THRESHOLD)
        return

    for _, row in significant_high.iterrows():
        logger.log(
            "significant_correlation_detected",
            metric=row["metric"],
            r=row["r"],
            q=row["q"],
            n=row["n"],
            threshold=CORRELATION_THRESHOLD
        )

def save_correlation_results(results_df: pd.DataFrame, output_path: str = "data/analysis/correlations.csv") -> None:
    """Save correlation results to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(path, index=False)
    logger.log("saved_correlation_results", path=str(path), count=len(results_df))

def perform_pca_on_metrics(df: pd.DataFrame, metric_cols: List[str]) -> Tuple[np.ndarray, np.ndarray, List[float]]:
    """
    Perform PCA on network metrics.
    Returns: factor_scores, loadings, explained_variance_ratio
    """
    valid_df = df[metric_cols].dropna()
    if len(valid_df) < 2:
        return np.array([]), np.array([]), []

    pca = PCA(n_components=2)
    scores = pca.fit_transform(valid_df)
    loadings = pca.components_
    var_ratio = pca.explained_variance_ratio_

    return scores, loadings, var_ratio

def save_pca_results(
    scores: np.ndarray,
    loadings: np.ndarray,
    var_ratio: List[float],
    subject_ids: List[str],
    output_scores_path: str = "data/analysis/factor_scores.csv",
    output_loadings_path: str = "data/analysis/pca_loadings.csv"
) -> None:
    """Save PCA results to CSV files."""
    # Save factor scores
    scores_df = pd.DataFrame(scores, columns=["pca_factor_1", "pca_factor_2"])
    scores_df.insert(0, "subject_id", subject_ids[:len(scores)])
    Path(output_scores_path).parent.mkdir(parents=True, exist_ok=True)
    scores_df.to_csv(output_scores_path, index=False)
    logger.log("saved_pca_scores", path=output_scores_path, count=len(scores_df))

    # Save loadings
    loadings_df = pd.DataFrame(loadings.T, columns=["component_1", "component_2"])
    # We don't have metric names here, assuming order matches input
    Path(output_loadings_path).parent.mkdir(parents=True, exist_ok=True)
    loadings_df.to_csv(output_loadings_path, index=False)
    logger.log("saved_pca_loadings", path=output_loadings_path)

def generate_full_metrics(
    metrics_df: pd.DataFrame,
    pca_scores_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge raw metrics with PCA factor scores.
    Ensures all data is available for FDR and reporting.
    """
    merged = pd.merge(
        metrics_df,
        pca_scores_df,
        on="subject_id",
        how="inner"
    )
    return merged

def save_full_metrics(df: pd.DataFrame, output_path: str = "data/analysis/full_metrics.csv") -> None:
    """Save full metrics dataframe to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.log("saved_full_metrics", path=str(path), count=len(df))

def main() -> None:
    """Main entry point for correlation analysis."""
    logger.log("starting_correlation_analysis")

    # 1. Load metrics
    try:
        metrics_df = load_metrics_data()
    except FileNotFoundError as e:
        logger.log("error_loading_metrics", error=str(e))
        # For testing, if file doesn't exist, we might need to generate synthetic data
        # But per constraints, we must use real data. If missing, we fail loudly.
        raise

    # 2. Define metric columns (adjust based on actual data schema)
    # Assuming T021/T022 produced these columns
    metric_cols = [
        "modularity",
        "global_efficiency",
        "participation_coef",
        "within_module_degree"
    ]
    available_cols = [c for c in metric_cols if c in metrics_df.columns]

    if not available_cols:
        logger.log("no_metric_columns_found", expected=metric_cols)
        return

    # 3. Run correlations with FD covariate
    corr_results = run_correlations_with_fd_covariate(metrics_df, available_cols)

    # 4. Log significant correlations (T027 implementation)
    log_significant_correlations(corr_results)

    # 5. Save correlation results
    save_correlation_results(corr_results)

    # 6. Perform PCA
    if len(available_cols) >= 2:
        scores, loadings, var_ratio = perform_pca_on_metrics(metrics_df, available_cols)
        if len(scores) > 0:
            save_pca_results(
                scores, loadings, var_ratio,
                metrics_df["subject_id"].tolist()[:len(scores)]
            )

            # 7. Generate and save full metrics
            scores_df = pd.read_csv("data/analysis/factor_scores.csv")
            full_df = generate_full_metrics(metrics_df, scores_df)
            save_full_metrics(full_df)
    else:
        logger.log("skipping_pca_insufficient_metrics")

    logger.log("correlation_analysis_complete")

if __name__ == "__main__":
    main()