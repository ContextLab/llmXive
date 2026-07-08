import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

__all__ = ["load_dataset_safe", "calculate_correlation", "run_sensitivity_analysis", "main"]

def load_dataset_safe(csv_path: str) -> pd.DataFrame:
    """
    Load a dataset CSV, returning an empty DataFrame on failure.

    Parameters
    ----------
    csv_path: str
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame or empty DataFrame if file not found.
    """
    try:
        df = pd.read_csv(csv_path)
        logging.info("Loaded dataset from %s", csv_path)
        return df
    except FileNotFoundError:
        logging.warning("Dataset not found at %s; returning empty DataFrame", csv_path)
        return pd.DataFrame()

def calculate_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
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

def run_sensitivity_analysis(
    pre_filter_path: str,
    primary_path: str,
    metric_column: str = "correlation_length",
) -> Dict[str, Any]:
    """
    Compute the change in correlation coefficient when depth‑confounded samples are excluded.

    Parameters
    ----------
    pre_filter_path: str
        Path to the pre‑filter dataset CSV.
    primary_path: str
        Path to the primary analysis dataset CSV.
    metric_column: str, optional
        Column name of the spatial metric to use (default ``'correlation_length'``).

    Returns
    -------
    Dict[str, Any]
        Dictionary containing ``'delta_r'`` and ``'significant'`` flag.
    """
    pre_df = load_dataset_safe(pre_filter_path)
    prim_df = load_dataset_safe(primary_path)

    if pre_df.empty or prim_df.empty:
        return {"delta_r": np.nan, "significant": False}

    r_full, _ = calculate_correlation(pre_df[metric_column].values, pre_df["PCE"].values)
    r_filtered, _ = calculate_correlation(prim_df[metric_column].values, prim_df["PCE"].values)
    delta = r_full - r_filtered
    # Simple significance heuristic: absolute change > 0.1
    significant = abs(delta) > 0.1
    return {"delta_r": delta, "significant": significant}

def main():
    """
    Placeholder CLI entry point for sensitivity analysis.
    """
    logging.info("Sensitivity analysis placeholder – no CLI implemented.")
