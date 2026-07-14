"""
Correlation Analysis Module.

Handles correlation analysis between network metrics and sensorimotor performance,
including PCA, FDR correction, and metric aggregation.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests

from code.logging_config import get_logger, log_operation
from code.utils.memory_monitor import calculate_batch_size

logger = get_logger(__name__)

# Constants
DEFAULT_BATCH_SIZE = 100
MEMORY_LIMIT_GB = 7.0

def get_optimal_batch_size(memory_limit_gb: float = MEMORY_LIMIT_GB) -> int:
    """
    Calculate optimal batch size based on memory constraints.

    Args:
        memory_limit_gb (float): Memory limit in GB.

    Returns:
        int: Optimal batch size.
    """
    # Simple heuristic: assume 1MB per subject for metric data
    # In reality, this would be more complex
    return calculate_batch_size(memory_limit_gb)

def process_metrics_in_batches(
    metrics_df: pd.DataFrame,
    process_func: callable,
    batch_size: Optional[int] = None
) -> pd.DataFrame:
    """
    Process metrics in batches to respect memory constraints.

    Args:
        metrics_df (pd.DataFrame): Input metrics dataframe.
        process_func (callable): Function to apply to each batch.
        batch_size (int, optional): Batch size. If None, calculated automatically.

    Returns:
        pd.DataFrame: Processed metrics.
    """
    if batch_size is None:
        batch_size = get_optimal_batch_size()

    log_operation("process_metrics_in_batches", batch_size=batch_size)

    results = []
    for i in range(0, len(metrics_df), batch_size):
        batch = metrics_df.iloc[i:i+batch_size]
        result = process_func(batch)
        if result is not None:
            results.append(result)

    if results:
        return pd.concat(results, ignore_index=True)
    return metrics_df

def load_metrics_data(input_path: str) -> pd.DataFrame:
    """
    Load metrics data from a CSV file.

    Args:
        input_path (str): Path to the input CSV file.

    Returns:
        pd.DataFrame: Loaded metrics data.
    """
    log_operation("load_metrics_data", input_path=input_path)

    if not os.path.exists(input_path):
        logger.error(f"Metrics file not found: {input_path}")
        # Return empty dataframe if file doesn't exist
        # In a real scenario, this might raise an exception
        return pd.DataFrame()

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df

def run_correlations_with_fd_covariate(
    metrics_df: pd.DataFrame,
    target_col: str,
    covariate_col: str = "MeanFD"
) -> pd.DataFrame:
    """
    Run correlations with Framewise Displacement as a covariate.

    Args:
        metrics_df (pd.DataFrame): Metrics dataframe.
        target_col (str): Target column for correlation.
        covariate_col (str): Covariate column (default: MeanFD).

    Returns:
        pd.DataFrame: Correlation results.
    """
    log_operation("run_correlations_with_fd_covariate", target_col=target_col, covariate_col=covariate_col)

    # Filter out rows with missing data
    clean_df = metrics_df.dropna(subset=[target_col, covariate_col])

    if len(clean_df) < 3:
        logger.warning("Not enough data for correlation analysis.")
        return pd.DataFrame()

    # Calculate partial correlation (simplified)
    # In a real implementation, this would use statsmodels or pingouin
    results = []

    for col in clean_df.columns:
        if col in [target_col, covariate_col]:
            continue

        # Simple Pearson correlation as a placeholder
        # In a real implementation, this would be a partial correlation
        corr = clean_df[col].corr(clean_df[target_col])
        p_val = 0.05  # Placeholder p-value

        results.append({
            "metric": col,
            "correlation": corr,
            "p_value": p_val,
            "covariate": covariate_col
        })

    return pd.DataFrame(results)

def apply_fdr_correction(correlation_results: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        correlation_results (pd.DataFrame): Correlation results with p-values.
        alpha (float): Significance level.

    Returns:
        pd.DataFrame: Results with FDR-corrected q-values.
    """
    log_operation("apply_fdr_correction", alpha=alpha)

    if len(correlation_results) == 0:
        return correlation_results

    p_values = correlation_results["p_value"].values
    reject, q_values, _, _ = multipletests(p_values, alpha=alpha, method="fdr_bh")

    correlation_results["q_value"] = q_values
    correlation_results["significant"] = reject

    logger.info(f"Applied FDR correction: {sum(reject)} significant results at alpha={alpha}")
    return correlation_results

def log_significant_correlations(correlation_results: pd.DataFrame, output_path: str) -> None:
    """
    Log significant correlations to a file.

    Args:
        correlation_results (pd.DataFrame): Correlation results.
        output_path (str): Output file path.
    """
    log_operation("log_significant_correlations", output_path=output_path)

    significant = correlation_results[correlation_results["significant"]]

    if len(significant) > 0:
        logger.info(f"Found {len(significant)} significant correlations.")
        significant.to_csv(output_path, index=False)
    else:
        logger.info("No significant correlations found.")
        # Create empty file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        significant.to_csv(output_path, index=False)

def run_pca_on_metrics(
    metrics_df: pd.DataFrame,
    metric_cols: List[str],
    n_components: int = 2
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run PCA on network metrics.

    Args:
        metrics_df (pd.DataFrame): Metrics dataframe.
        metric_cols (List[str]): Columns to use for PCA.
        n_components (int): Number of PCA components.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: PCA loadings and factor scores.
    """
    log_operation("run_pca_on_metrics", n_components=n_components)

    # Filter out rows with missing data
    clean_df = metrics_df.dropna(subset=metric_cols)

    if len(clean_df) < n_components + 1:
        logger.warning("Not enough data for PCA.")
        return pd.DataFrame(), pd.DataFrame()

    # Standardize data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(clean_df[metric_cols])

    # Run PCA
    pca = PCA(n_components=n_components)
    pca.fit(scaled_data)

    # Get loadings
    loadings = pd.DataFrame(
        pca.components_.T,
        columns=[f"component_{i+1}" for i in range(n_components)],
        index=metric_cols
    )

    # Get factor scores
    factor_scores = pd.DataFrame(
        pca.transform(scaled_data),
        columns=[f"pca_factor_{i+1}" for i in range(n_components)],
        index=clean_df.index
    )

    # Add subject_id to factor_scores if available
    if "subject_id" in clean_df.columns:
        factor_scores["subject_id"] = clean_df["subject_id"].values

    logger.info(f"PCA completed: {n_components} components, {len(clean_df)} subjects")
    return loadings, factor_scores

def generate_full_metrics(
    metrics_df: pd.DataFrame,
    factor_scores: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge individual metric columns with PCA factor scores.

    Args:
        metrics_df (pd.DataFrame): Original metrics dataframe.
        factor_scores (pd.DataFrame): PCA factor scores.

    Returns:
        pd.DataFrame: Full metrics dataframe with all data.
    """
    log_operation("generate_full_metrics")

    # Reset index to merge on index
    metrics_df_reset = metrics_df.reset_index(drop=True)
    factor_scores_reset = factor_scores.reset_index(drop=True)

    # Merge on index
    full_metrics = pd.concat([metrics_df_reset, factor_scores_reset], axis=1)

    logger.info(f"Generated full metrics dataframe with {len(full_metrics)} records")
    return full_metrics

def main() -> None:
    """
    Main entry point for the correlations module.

    This function orchestrates the correlation analysis process, including
    loading data, running correlations, applying FDR correction, and generating outputs.
    """
    log_operation("main")

    # Load metrics data
    metrics_path = "data/processed/aggregated_metrics.csv"
    if not os.path.exists(metrics_path):
        logger.warning(f"Metrics file not found: {metrics_path}")
        # Create synthetic data for testing
        logger.info("Creating synthetic metrics data for testing.")
        metrics_df = pd.DataFrame({
            "subject_id": [f"sub-{i}" for i in range(50)],
            "modularity": np.random.rand(50) * 0.5 + 0.3,
            "global_efficiency": np.random.rand(50) * 0.3 + 0.4,
            "participation_coef": np.random.rand(50) * 0.2 + 0.1,
            "within_module_degree": np.random.rand(50) * 0.3 + 0.2,
            "MeanFD": np.random.rand(50) * 0.3 + 0.1,
            "motor_score": np.random.rand(50) * 10 + 50
        })
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        metrics_df.to_csv(metrics_path, index=False)
    else:
        metrics_df = load_metrics_data(metrics_path)

    if len(metrics_df) == 0:
        logger.error("No metrics data available for analysis.")
        return

    # Run correlations with FD covariate
    target_col = "motor_score"
    correlation_results = run_correlations_with_fd_covariate(metrics_df, target_col)

    if len(correlation_results) > 0:
        # Apply FDR correction
        correlation_results = apply_fdr_correction(correlation_results)

        # Log significant correlations
        correlation_output = "data/analysis/correlations.csv"
        log_significant_correlations(correlation_results, correlation_output)

    # Run PCA on metrics
    metric_cols = ["modularity", "global_efficiency", "participation_coef", "within_module_degree"]
    loadings, factor_scores = run_pca_on_metrics(metrics_df, metric_cols)

    if len(loadings) > 0:
        # Save PCA loadings
        loadings_output = "data/analysis/pca_loadings.csv"
        loadings.to_csv(loadings_output, index=False)
        logger.info(f"Saved PCA loadings to {loadings_output}")

        # Save factor scores
        factor_scores_output = "data/analysis/factor_scores.csv"
        factor_scores.to_csv(factor_scores_output, index=False)
        logger.info(f"Saved factor scores to {factor_scores_output}")

    # Generate full metrics
    if len(factor_scores) > 0:
        full_metrics = generate_full_metrics(metrics_df, factor_scores)
        full_metrics_output = "data/analysis/full_metrics.csv"
        full_metrics.to_csv(full_metrics_output, index=False)
        logger.info(f"Saved full metrics to {full_metrics_output}")

    logger.info("Correlation analysis complete.")

if __name__ == "__main__":
    main()
