import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Optional, List, Union

__all__ = [
    "load_primary_dataset",
    "calculate_correlation",
    "benjamini_hochberg_correction",
    "compute_correlations",
    "write_correlation_results",
    "main",
]

def load_primary_dataset(csv_path: str) -> pd.DataFrame:
    """
    Load the primary analysis dataset.

    Parameters
    ----------
    csv_path: str
        Path to the CSV file produced by ``code/modeling/filter.py``.

    Returns
    -------
    pd.DataFrame
        DataFrame with all required columns.
    """
    logging.info("Loading primary dataset from %s", csv_path)
    return pd.read_csv(csv_path)

def calculate_correlation(
    x: np.ndarray, y: np.ndarray
) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient and p‑value.

    Parameters
    ----------
    x: np.ndarray
        First variable.
    y: np.ndarray
        Second variable.

    Returns
    -------
    Tuple[float, float]
        (r, p_value)
    """
    from scipy.stats import pearsonr

    r, p = pearsonr(x, y)
    return r, p

def benjamini_hochberg_correction(pvals: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Perform Benjamini‑Hochberg FDR correction.

    Parameters
    ----------
    pvals: List[float]
        List of raw p‑values.
    alpha: float, optional
        Desired false discovery rate (default 0.05).

    Returns
    -------
    List[bool]
        Boolean mask indicating which hypotheses are rejected (True = significant).
    """
    m = len(pvals)
    sorted_idx = np.argsort(pvals)
    sorted_p = np.array(pvals)[sorted_idx]
    thresholds = (np.arange(1, m + 1) / m) * alpha
    below = sorted_p <= thresholds
    if not below.any():
        return [False] * m
    max_i = np.max(np.where(below))
    reject = np.zeros(m, dtype=bool)
    reject[sorted_idx[: max_i + 1]] = True
    return reject.tolist()

def compute_correlations(
    df: pd.DataFrame,
    metric_cols: List[str],
    target_col: str = "PCE",
) -> pd.DataFrame:
    """
    Compute Pearson and Spearman correlations between each spatial metric and the target performance metric.

    Parameters
    ----------
    df: pd.DataFrame
        Primary dataset containing metric columns and the target column.
    metric_cols: List[str]
        Names of columns holding spatial metrics.
    target_col: str, optional
        Column name of the performance metric (default ``'PCE'``).

    Returns
    -------
    pd.DataFrame
        DataFrame with rows for each metric and columns:
        ``['metric', 'pearson_r', 'pearson_p', 'spearman_r', 'spearman_p']``.
    """
    from scipy.stats import spearmanr

    results = []
    for col in metric_cols:
        x = df[col].values
        y = df[target_col].values
        pear_r, pear_p = calculate_correlation(x, y)
        spearman_r, spearman_p = spearmanr(x, y)
        results.append(
            {
                "metric": col,
                "pearson_r": pear_r,
                "pearson_p": pear_p,
                "spearman_r": spearman_r,
                "spearman_p": spearman_p,
            }
        )
    return pd.DataFrame(results)

def write_correlation_results(df: pd.DataFrame, out_path: str) -> None:
    """
    Write correlation results to CSV.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame produced by ``compute_correlations``.
    out_path: str
        Destination CSV file path.
    """
    df.to_csv(out_path, index=False)
    logging.info("Correlation results saved to %s", out_path)

def main(input_csv: str, output_csv: str, metric_columns: List[str]) -> None:
    """
    End‑to‑end entry point for correlation analysis.

    Parameters
    ----------
    input_csv: str
        Path to the primary analysis dataset CSV.
    output_csv: str
        Destination path for the correlation results CSV.
    metric_columns: List[str]
        List of column names to treat as spatial metrics.
    """
    df = load_primary_dataset(input_csv)
    corr_df = compute_correlations(df, metric_columns)
    write_correlation_results(corr_df, output_csv)
