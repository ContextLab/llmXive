import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
from utils.io import save_parquet, load_parquet, save_json, load_json, ensure_dir

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
__all__ = [
    "regress_confounds",
    "compute_static_connectivity",
    "compute_static_metrics",
    "compute_dynamic_connectivity",
    "compute_reconfiguration_rate",
    "compute_icc",
    "run_sensitivity_analysis",
    "main",
]

# ----------------------------------------------------------------------
# Placeholder / minimal implementations for existing functions
# ----------------------------------------------------------------------
def regress_confounds(time_series: np.ndarray, confounds: np.ndarray) -> np.ndarray:
    """
    Regress out confound variables from the time series.

    Parameters
    ----------
    time_series : np.ndarray
        2D array (timepoints x variables) of BOLD signals.
    confounds : np.ndarray
        2D array (timepoints x confound variables).

    Returns
    -------
    np.ndarray
        Residuals after linear regression of confounds.
    """
    if time_series.shape[0] != confounds.shape[0]:
        raise ValueError("Time series and confounds must have the same number of timepoints.")
    # Simple OLS regression using numpy.linalg.lstsq
    X = np.column_stack([confounds, np.ones(confounds.shape[0])])
    beta, _, _, _ = np.linalg.lstsq(X, time_series, rcond=None)
    fitted = X @ beta
    residuals = time_series - fitted
    return residuals

def compute_static_connectivity(time_series: np.ndarray) -> np.ndarray:
    """
    Compute static functional connectivity (Pearson correlation) matrix.

    Parameters
    ----------
    time_series : np.ndarray
        2D array (timepoints x ROIs).

    Returns
    -------
    np.ndarray
        Correlation matrix (ROIs x ROIs).
    """
    if time_series.ndim != 2:
        raise ValueError("time_series must be a 2D array (timepoints x ROIs).")
    corr = np.corrcoef(time_series.T)
    return corr

def compute_static_metrics(matrix: np.ndarray, network_map: Dict[int, str]) -> Dict[str, float]:
    """
    Compute static network metrics for predefined networks.

    This placeholder returns dummy values; real implementation should
    compute metrics such as global efficiency, modularity, etc.
    """
    # Placeholder: return the mean of the upper triangle as a dummy metric
    triu = matrix[np.triu_indices_from(matrix, k=1)]
    return {"mean_connectivity": float(np.mean(triu))}

def compute_dynamic_connectivity(
    time_series: np.ndarray, window_size: int, step: int
) -> List[np.ndarray]:
    """
    Compute sliding-window dynamic connectivity matrices.

    Parameters
    ----------
    time_series : np.ndarray
        2D array (timepoints x ROIs).
    window_size : int
        Number of TRs in each window.
    step : int
        Step size between windows.

    Returns
    -------
    List[np.ndarray]
        List of correlation matrices for each window.
    """
    n_timepoints = time_series.shape[0]
    windows = []
    for start in range(0, n_timepoints - window_size + 1, step):
        window_ts = time_series[start : start + window_size, :]
        corr = np.corrcoef(window_ts.T)
        windows.append(corr)
    return windows

def compute_reconfiguration_rate(dynamic_matrices: List[np.ndarray]) -> float:
    """
    Compute a simple reconfiguration rate metric.

    This placeholder computes the average Frobenius norm difference
    between successive windows.
    """
    if len(dynamic_matrices) < 2:
        return 0.0
    diffs = [
        np.linalg.norm(dynamic_matrices[i] - dynamic_matrices[i - 1], ord="fro")
        for i in range(1, len(dynamic_matrices))
    ]
    return float(np.mean(diffs))

# ----------------------------------------------------------------------
# ICC computation
# ----------------------------------------------------------------------
def compute_icc(metrics: List[float]) -> float:
    """
    Compute the Intraclass Correlation Coefficient (ICC) for a list of
    metric values obtained across different sliding‑window sizes.

    The implementation uses the two‑way random effects model (ICC2)
    provided by the ``pingouin`` library. If ``pingouin`` is not
    installed, an informative ImportError is raised.

    Parameters
    ----------
    metrics : List[float]
        Metric values (e.g., reconfiguration rates) for each window size.

    Returns
    -------
    float
        The ICC value (between 0 and 1). Higher values indicate greater
        reliability/stability of the metric across window sizes.
    """
    if not metrics:
        raise ValueError("The metrics list must contain at least one value.")

    try:
        import pingouin as pg
    except ImportError as exc:
        raise ImportError(
            "The 'pingouin' package is required for ICC computation. "
            "Install it via 'pip install pingouin'."
        ) from exc

    # Build a DataFrame compatible with pingouin's intraclass_corr function.
    # All metrics belong to a single dummy subject; each metric is treated as
    # a rating from a different rater (i.e., window size).
    df = pd.DataFrame(
        {
            "subject": [1] * len(metrics),          # Dummy subject identifier
            "rater": list(range(len(metrics))),    # Rater ID = window index
            "rating": metrics,
        }
    )

    icc_df = pg.intraclass_corr(
        data=df,
        targets="subject",
        raters="rater",
        ratings="rating",
    )

    # Select the ICC2 (two‑way random effects, single rater) row.
    icc_row = icc_df.loc[icc_df["Type"] == "ICC2"]
    if icc_row.empty:
        raise RuntimeError("Failed to compute ICC2; pingouin returned no result.")
    icc_value = icc_row["ICC"].values[0]
    return float(icc_value)

# ----------------------------------------------------------------------
# Sensitivity analysis (placeholder)
# ----------------------------------------------------------------------
def run_sensitivity_analysis(
    time_series: np.ndarray, window_sizes: List[int]
) -> Dict[int, float]:
    """
    Run sensitivity analysis over a list of window sizes.

    This placeholder computes the ICC of the reconfiguration rate
    for each window size and returns a mapping from window size to ICC.
    """
    results = {}
    for ws in window_sizes:
        dyn = compute_dynamic_connectivity(time_series, window_size=ws, step=5)
        rate = compute_reconfiguration_rate(dyn)
        # For the purpose of this placeholder we treat the single rate as a list
        # with duplicate values to allow ICC computation (which needs >1 value).
        icc = compute_icc([rate, rate])
        results[ws] = icc
    return results

# ----------------------------------------------------------------------
# Main entry point (placeholder)
# ----------------------------------------------------------------------
def main() -> None:
    """
    Placeholder main function for the metrics module.
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Metrics module loaded. No standalone execution defined.")
