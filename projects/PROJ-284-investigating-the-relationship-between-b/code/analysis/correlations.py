"""
Correlation analysis module for network metrics and sensorimotor performance.
Implements dynamic batch sizing for memory-constrained matrix computations.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr

from code.config import get_config
from code.utils.memory_monitor import estimate_memory_usage, get_available_memory
from code.logging_config import get_logger

# Configuration constants
MEMORY_LIMIT_GB = 7.0
BATCH_SIZE_DEFAULT = 50
CORRELATION_THRESHOLD = 0.3

logger = get_logger(__name__)


def load_metrics_data(file_path: str = "data/analysis/full_metrics.csv") -> pd.DataFrame:
    """Load metrics data from CSV file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    return pd.read_csv(file_path)


def partial_correlation(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray
) -> Tuple[float, float]:
    """
    Calculate partial correlation between x and y, controlling for z.

    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    # Linear regression of x on z
    x_resid = stats.linregress(z, x).intercept + stats.linregress(z, x).slope * z
    x_resid = x - x_resid

    # Linear regression of y on z
    y_resid = stats.linregress(z, y).intercept + stats.linregress(z, y).slope * z
    y_resid = y - y_resid

    # Correlation of residuals
    r, p = pearsonr(x_resid, y_resid)
    return r, p


def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Returns:
        List of booleans indicating significance after correction
    """
    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values with original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = [p_values[i] for i in sorted_indices]

    # Calculate critical values
    critical_values = [(i + 1) * alpha / n for i in range(n)]

    # Find largest k such that p_(k) <= critical_value_(k)
    significant = [False] * n
    max_k = -1
    for i in range(n):
        if sorted_p[i] <= critical_values[i]:
            max_k = i

    if max_k >= 0:
        threshold = sorted_p[max_k]
        for i in range(n):
            if p_values[i] <= threshold:
                significant[sorted_indices[i]] = True

    return significant


def run_metric_correlations(
    df: pd.DataFrame,
    metric_cols: List[str],
    target_col: str = "motor_score",
    covariate_col: str = "fd",
    batch_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run correlations between metrics and target, controlling for covariate.

    Implements dynamic batch sizing to respect memory constraints.

    Args:
        df: DataFrame with metrics and target/covariate columns
        metric_cols: List of metric column names to correlate
        target_col: Name of target variable column
        covariate_col: Name of covariate column to control for
        batch_size: Optional override for batch size (auto-calculated if None)

    Returns:
        Dictionary with correlation results including r, p, q, significant
    """
    # Determine batch size dynamically if not provided
    if batch_size is None:
        batch_size = _calculate_optimal_batch_size(df, metric_cols)

    logger.log("correlation_batch_start", batch_size=batch_size, num_metrics=len(metric_cols))

    results = []
    total_batches = (len(metric_cols) + batch_size - 1) // batch_size

    for i in range(0, len(metric_cols), batch_size):
        batch_metrics = metric_cols[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        logger.log("correlation_batch_process", batch=batch_num, total=total_batches, metrics=batch_metrics)

        for metric in batch_metrics:
            if metric not in df.columns or target_col not in df.columns or covariate_col not in df.columns:
                logger.log("correlation_skip_missing", metric=metric, reason="column_not_found")
                continue

            x = df[metric].dropna().values
            y = df[target_col].dropna().values
            z = df[covariate_col].dropna().values

            # Ensure arrays are aligned
            valid_mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
            if np.sum(valid_mask) < 3:
                logger.log("correlation_skip_insufficient", metric=metric, valid_count=np.sum(valid_mask))
                continue

            x_valid = x[valid_mask]
            y_valid = y[valid_mask]
            z_valid = z[valid_mask]

            try:
                r, p = partial_correlation(x_valid, y_valid, z_valid)
                results.append({
                    "metric_name": metric,
                    "r": r,
                    "p": p,
                    "covariate_controlled": True,
                    "n_samples": len(x_valid)
                })
            except Exception as e:
                logger.log("correlation_error", metric=metric, error=str(e))
                continue

    # Apply FDR correction
    if results:
        p_values = [r["p"] for r in results]
        significant_flags = apply_fdr_correction(p_values)

        for i, sig in enumerate(significant_flags):
            results[i]["q"] = p_values[i] * len(p_values) / (i + 1) if p_values[i] > 0 else 0.0
            results[i]["significant"] = sig

            # Log significant correlations
            if sig and abs(results[i]["r"]) > CORRELATION_THRESHOLD:
                logger.log("significant_correlation_found",
                           metric=results[i]["metric_name"],
                           r=results[i]["r"],
                           q=results[i]["q"])

    return {
        "results": results,
        "batch_size_used": batch_size,
        "total_metrics_processed": len(metric_cols),
        "significant_count": sum(1 for r in results if r.get("significant", False))
    }


def compute_and_save_correlation_matrix(
    df: pd.DataFrame,
    metric_cols: List[str],
    output_path: str = "data/analysis/correlation_matrix.csv"
) -> pd.DataFrame:
    """
    Compute correlation matrix for metrics and save to CSV.
    Uses batch processing for memory efficiency.

    Args:
        df: DataFrame with metric columns
        metric_cols: List of metric column names
        output_path: Path to save the correlation matrix

    Returns:
        Correlation matrix as DataFrame
    """
    batch_size = _calculate_optimal_batch_size(df, metric_cols)
    logger.log("correlation_matrix_batch_start", batch_size=batch_size)

    # Initialize result matrix
    corr_matrix = np.zeros((len(metric_cols), len(metric_cols)))

    for i in range(0, len(metric_cols), batch_size):
        batch_end_i = min(i + batch_size, len(metric_cols))
        for j in range(0, len(metric_cols), batch_size):
            batch_end_j = min(j + batch_size, len(metric_cols))

            # Compute correlations for this block
            for ii in range(i, batch_end_i):
                for jj in range(j, batch_end_j):
                    if ii == jj:
                        corr_matrix[ii, jj] = 1.0
                    else:
                        x = df[metric_cols[ii]].dropna().values
                        y = df[metric_cols[jj]].dropna().values
                        min_len = min(len(x), len(y))
                        if min_len > 1:
                            r, _ = pearsonr(x[:min_len], y[:min_len])
                            corr_matrix[ii, jj] = r
                            corr_matrix[jj, ii] = r
                        else:
                            corr_matrix[ii, jj] = np.nan
                            corr_matrix[jj, ii] = np.nan

    # Convert to DataFrame
    corr_df = pd.DataFrame(
        corr_matrix,
        index=metric_cols,
        columns=metric_cols
    )

    # Save to CSV
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    corr_df.to_csv(output_path)
    logger.log("correlation_matrix_saved", path=output_path)

    return corr_df


def _calculate_optimal_batch_size(df: pd.DataFrame, metric_cols: List[str]) -> int:
    """
    Calculate optimal batch size based on available memory and data size.

    Args:
        df: DataFrame containing the data
        metric_cols: List of metric columns to process

    Returns:
        Optimal batch size
    """
    available_gb = get_available_memory()
    memory_limit_gb = min(available_gb, MEMORY_LIMIT_GB)

    # Estimate memory per metric row (float64 * number of metrics + overhead)
    n_samples = len(df)
    bytes_per_row = len(metric_cols) * 8 + 100  # 8 bytes per float64 + overhead
    memory_per_batch_gb = (bytes_per_row * BATCH_SIZE_DEFAULT) / (1024 ** 3)

    # Calculate max batch size that fits in memory with 80% safety margin
    max_batch_size = int((memory_limit_gb * 0.8) / memory_per_batch_gb * BATCH_SIZE_DEFAULT)

    # Clamp to reasonable bounds
    batch_size = max(10, min(max_batch_size, BATCH_SIZE_DEFAULT * 10))

    # Ensure we don't exceed the number of metrics
    batch_size = min(batch_size, len(metric_cols))

    logger.log("batch_size_calculated",
               available_gb=available_gb,
               limit_gb=memory_limit_gb,
               calculated_batch_size=batch_size)

    return batch_size


def main():
    """Main entry point for correlation analysis."""
    try:
        # Load data
        df = load_metrics_data()
        logger.log("data_loaded", row_count=len(df), column_count=len(df.columns))

        # Define metric columns (excluding metadata columns)
        metric_cols = [
            "modularity", "global_efficiency", "participation_coef", "within_module_degree"
        ]

        # Filter to only existing columns
        metric_cols = [col for col in metric_cols if col in df.columns]

        if not metric_cols:
            logger.log("no_metrics_found", available_columns=list(df.columns))
            return

        # Run correlations
        results = run_metric_correlations(df, metric_cols)

        # Save results
        output_path = "data/analysis/correlation_results.csv"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(results["results"]).to_csv(output_path, index=False)

        logger.log("analysis_complete",
                   output_path=output_path,
                   significant_count=results["significant_count"])

        print(f"Correlation analysis complete. Results saved to {output_path}")
        print(f"Significant correlations found: {results['significant_count']}")

    except Exception as e:
        logger.log("analysis_failed", error=str(e))
        raise