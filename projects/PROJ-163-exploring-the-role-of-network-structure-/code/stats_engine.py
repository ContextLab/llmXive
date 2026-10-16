"""
Statistical Engine for Cross-Sectional Analysis of Qubit Network Structure and Performance.

This module implements the statistical correlation and robustness analysis logic.
It enforces the cross‑sectional constraint: topology and performance metrics are
extracted from the same calibration snapshot. Historical time‑window logic for
topology is disabled.

The analysis operates on real data loaded from ``data/processed/*.csv`` files.
No synthetic data generation is permitted.
"""

import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

# Constants
CROSS_SECTIONAL_MODE = True
logger = logging.getLogger(__name__)

def load_and_merge_metrics(
    performance_path: str = "data/processed/performance_metrics.csv",
    graph_path: str = "data/processed/graph_metrics.csv"
) -> pd.DataFrame:
    """
    Load and merge performance metrics and graph metrics by ``device_id``.

    The function joins the two datasets on ``device_id`` ONLY, ensuring that we
    are correlating metrics from the same calibration snapshot (cross‑sectional
    analysis).

    Parameters
    ----------
    performance_path : str
        Path to the performance metrics CSV.
    graph_path : str
        Path to the graph metrics CSV.

    Returns
    -------
    pd.DataFrame
        A merged DataFrame containing performance and graph metrics.

    Raises
    ------
    FileNotFoundError
        If either input file does not exist.
    ValueError
        If the merged DataFrame is empty (no overlapping ``device_id`` values).
    """
    if not os.path.exists(performance_path):
        raise FileNotFoundError(f"Performance metrics file not found: {performance_path}")
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph metrics file not found: {graph_path}")

    logger.info(f"Loading performance metrics from {performance_path}")
    perf_df = pd.read_csv(performance_path)

    logger.info(f"Loading graph metrics from {graph_path}")
    graph_df = pd.read_csv(graph_path)

    # Pivot graph metrics to wide format for merging.
    # Expected columns in ``graph_df``: device_id, metric_name, value, is_finite
    graph_wide = (
        graph_df.pivot_table(index="device_id", columns="metric_name", values="value", aggfunc="first")
        .reset_index()
    )

    # Merge on device_id using the correct pandas API.
    merged_df = pd.merge(left=perf_df, right=graph_wide, on="device_id", how="inner")

    if merged_df.empty:
        raise ValueError("Merged DataFrame is empty. Check for overlapping device_ids.")

    logger.info(f"Merged dataset shape: {merged_df.shape}")
    logger.info(f"Columns in merged dataset: {list(merged_df.columns)}")

    return merged_df

def compute_spearman_correlations(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Spearman rank‑correlations between all pairs of numeric columns.

    Parameters
    ----------
    merged_df : pd.DataFrame
        The merged DataFrame from :func:`load_and_merge_metrics`.

    Returns
    -------
    pd.DataFrame
        Columns: ``metric_a``, ``metric_b``, ``rho``, ``p_value``.
    """
    # Identify numeric columns (int, float, etc.)
    numeric_cols = merged_df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) < 2:
        logger.warning("Not enough numeric columns to compute correlations.")
        return pd.DataFrame(columns=["metric_a", "metric_b", "rho", "p_value"])

    correlations = []

    for i, col_a in enumerate(numeric_cols):
        for col_b in numeric_cols[i + 1 :]:
            # Drop rows with NaNs in either column
            valid_data = merged_df[[col_a, col_b]].dropna()
            if len(valid_data) < 3:
                logger.warning(f"Insufficient data points for {col_a} vs {col_b}")
                continue

            rho, p_value = spearmanr(valid_data[col_a], valid_data[col_b])

            correlations.append(
                {
                    "metric_a": col_a,
                    "metric_b": col_b,
                    "rho": rho,
                    "p_value": p_value,
                }
            )

    return pd.DataFrame(correlations)

def apply_benjamini_hochberg_fdr(correlation_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini‑Hochberg FDR correction to the ``p_value`` column.

    Parameters
    ----------
    correlation_df : pd.DataFrame
        DataFrame that contains a ``p_value`` column.
    alpha : float, optional
        Desired false‑discovery rate (default 0.05).

    Returns
    -------
    pd.DataFrame
        The input DataFrame with two new columns: ``adj_p_value`` and
        ``is_significant`` (boolean).
    """
    if correlation_df.empty:
        return correlation_df

    p_values = correlation_df["p_value"].values
    rejected, adj_p_values, _, _ = multipletests(p_values, alpha=alpha, method="fdr_bh")

    correlation_df = correlation_df.copy()
    correlation_df["adj_p_value"] = adj_p_values
    correlation_df["is_significant"] = rejected

    return correlation_df

def save_correlation_results(
    correlation_df: pd.DataFrame,
    output_path: str = "data/processed/correlation_results.csv",
) -> None:
    """
    Persist the correlation results to a CSV file.

    Parameters
    ----------
    correlation_df : pd.DataFrame
        DataFrame containing correlation results (including FDR columns).
    output_path : str, optional
        Destination path for the CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    correlation_df.to_csv(output_path, index=False)
    logger.info(f"Saved correlation results to {output_path}")

# ----------------------------------------------------------------------
# Placeholder / future‑implementation hooks (not required for T004)
# ----------------------------------------------------------------------
def robustness_check_lodo(merged_df: pd.DataFrame, correlation_df: pd.DataFrame) -> List[Dict]:
    """Leave‑One‑Device‑Out robustness check (stub)."""
    logger.info("Performing Leave-One-Device-Out analysis... (stub)")
    return []

def robustness_check_variance_stability(merged_df: pd.DataFrame) -> Dict:
    """Variance stability check (stub)."""
    logger.info("Checking variance stability... (stub)")
    return {}

def power_analysis(merged_df: pd.DataFrame, correlation_df: pd.DataFrame) -> Dict:
    """Statistical power analysis (stub)."""
    logger.info("Performing power analysis... (stub)")
    return {}

def save_mdes_report(mdes_results: Dict, output_path: str = "docs/mdes_report.json") -> None:
    """Save MDES report JSON (stub)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        import json

        json.dump(mdes_results, f, indent=2)
    logger.info(f"Saved MDES report to {output_path}")

def main() -> None:
    """
    Entry point for the stats engine.

    Executes the full correlation pipeline:
    1. Load and merge performance & graph metrics.
    2. Compute Spearman correlations.
    3. Apply Benjamini‑Hochberg FDR correction.
    4. Persist the results.
    """
    logging.basicConfig(level=logging.INFO)

    try:
        merged_df = load_and_merge_metrics()
        corr_df = compute_spearman_correlations(merged_df)
        corr_df = apply_benjamini_hochberg_fdr(corr_df)
        save_correlation_results(corr_df)
        logger.info("Stats engine completed successfully.")
    except Exception as e:
        logger.error(f"Stats engine failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
