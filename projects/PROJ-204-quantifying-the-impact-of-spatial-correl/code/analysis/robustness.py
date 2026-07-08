import os
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from scipy.stats import pearsonr

__all__ = ["calculate_correlation", "perform_leave_one_out_cv", "main"]

def calculate_correlation(
    x: np.ndarray, y: np.ndarray
) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient and two‑tailed p‑value.

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
    logging.debug("Calculating Pearson correlation")
    r, p = pearsonr(x, y)
    return r, p

def perform_leave_one_out_cv(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
) -> pd.DataFrame:
    """
    Perform leave‑one‑out cross‑validation for correlation.

    For each row, the function removes that row, recomputes the Pearson
    correlation on the remaining data, and records the resulting r value.

    Parameters
    ----------
    df: pd.DataFrame
        Input data containing ``x_col`` and ``y_col``.
    x_col: str
        Name of the predictor column.
    y_col: str
        Name of the response column.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``'sample_id'`` and ``'loo_r'``.
    """
    results = []
    for idx in df.index:
        train = df.drop(idx)
        r, _ = calculate_correlation(train[x_col].values, train[y_col].values)
        results.append({"sample_id": df.at[idx, "sample_id"], "loo_r": r})
    return pd.DataFrame(results)

def main(input_csv: str, output_csv: str, x_col: str = "metric", y_col: str = "PCE") -> None:
    """
    Run robustness analysis on a dataset.

    Parameters
    ----------
    input_csv: str
        Path to the CSV file containing the dataset.
    output_csv: str
        Destination path for the LOO results.
    x_col: str, optional
        Column name for the metric (default ``'metric'``).
    y_col: str, optional
        Column name for the performance metric (default ``'PCE'``).
    """
    logging.info("Reading dataset from %s", input_csv)
    df = pd.read_csv(input_csv)
    loo_df = perform_leave_one_out_cv(df, x_col, y_col)
    loo_df.to_csv(output_csv, index=False)
    logging.info("Leave‑one‑out results written to %s", output_csv)
