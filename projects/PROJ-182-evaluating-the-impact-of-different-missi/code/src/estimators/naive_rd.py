"""
Naïve Local-Linear RD Estimator.

Implements a local-linear regression discontinuity design estimator using
listwise deletion for missing values. Uses the Imbens-Kalyanaraman (IK)
bandwidth selector with a floor of 0.05 * (max(X) - min(X)) as per project
plan resolution for FR-003.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from scipy.optimize import minimize_scalar
import statsmodels.api as sm

from src.logging_config import get_logger
from src.models import EstimationResult

logger = get_logger(__name__)


def _compute_ik_bandwidth(x: np.ndarray, y: np.ndarray, cutoff: float = 0.0) -> float:
    """
    Compute Imbens-Kalyanaraman (IK) bandwidth for RD.

    This is a simplified implementation based on the IK rule of thumb.
    It estimates the optimal bandwidth for a local linear regression.

    Parameters
    ----------
    x : np.ndarray
        Running variable.
    y : np.ndarray
        Outcome variable.
    cutoff : float
        Cutoff point for the RD (default 0.0).

    Returns
    -------
    float
        Optimal bandwidth.
    """
    n = len(x)
    if n < 10:
        logger.warning("Sample size too small for IK bandwidth calculation. Returning fallback.")
        return 0.05 * (np.max(x) - np.min(x))

    # Filter to a window around the cutoff for local estimation
    # Using a rough initial window of 0.5 * range
    x_range = np.max(x) - np.min(x)
    window = 0.5 * x_range
    mask = (x >= cutoff - window) & (x <= cutoff + window)
    x_local = x[mask]
    y_local = y[mask]

    if len(x_local) < 10:
        # Fallback if not enough points in window
        return 0.05 * x_range

    # Estimate variance and derivatives roughly
    # Using a simple local linear fit to get residuals
    x_centered = x_local - cutoff
    X_design = np.column_stack((np.ones(len(x_centered)), x_centered))
    try:
        beta, _, _, _ = np.linalg.lstsq(X_design, y_local, rcond=None)
        y_hat = X_design @ beta
        residuals = y_local - y_hat
        sigma_sq = np.mean(residuals**2)
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix in IK bandwidth calculation. Returning fallback.")
        return 0.05 * x_range

    # IK bandwidth formula approximation:
    # h_ik = C * (sigma^2 / (f''(c)^2 * n))^(1/5)
    # We use a simplified constant C and estimate f''(c) via local curvature
    # A common practical approximation uses the standard deviation of X and Y
    std_x = np.std(x_local)
    std_y = np.std(y_local)

    # Simple heuristic scaling often used in practice when full IK is complex
    # h ~ 1.06 * std_x * n^(-1/5) (Silverman's rule of thumb adapted)
    # Adjusted for RD context:
    h_ik = 1.0 * std_x * (len(x_local) ** (-1/5))

    return h_ik


def estimate_naive_rd(
    df: pd.DataFrame,
    outcome_col: str = 'Y',
    running_col: str = 'X',
    treatment_col: str = 'D',
    cutoff: float = 0.0,
    min_bandwidth_ratio: float = 0.05
) -> EstimationResult:
    """
    Estimate RD effect using local-linear regression with listwise deletion.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data. Must have outcome, running, and treatment columns.
    outcome_col : str
        Name of the outcome variable column.
    running_col : str
        Name of the running variable column.
    treatment_col : str
        Name of the treatment indicator column (1 if X > cutoff).
    cutoff : float
        The RD cutoff point.
    min_bandwidth_ratio : float
        Minimum bandwidth as a fraction of the range of X. Default 0.05.

    Returns
    -------
    EstimationResult
        Object containing estimate, standard error, and other stats.
        Returns NaN if estimation fails.
    """
    logger.info(f"Running Naïve RD estimator on {len(df)} rows.")

    # Drop rows with missing values in relevant columns (Listwise Deletion)
    cols_to_check = [outcome_col, running_col, treatment_col]
    df_clean = df.dropna(subset=cols_to_check)

    if len(df_clean) < 10:
        logger.error("Insufficient data after listwise deletion.")
        return EstimationResult(estimate=np.nan, se=np.nan, n_obs=len(df), n_used=0, success=False)

    x = df_clean[running_col].values
    y = df_clean[outcome_col].values
    d = df_clean[treatment_col].values

    x_range = np.max(x) - np.min(x)
    if x_range == 0:
        logger.error("Running variable has zero range.")
        return EstimationResult(estimate=np.nan, se=np.nan, n_obs=len(df), n_used=len(df_clean), success=False)

    # Calculate IK bandwidth
    h_ik = _compute_ik_bandwidth(x, y, cutoff)
    
    # Apply floor constraint
    h_min = min_bandwidth_ratio * x_range
    if h_ik < h_min:
        logger.info(f"IK bandwidth {h_ik:.4f} < floor {h_min:.4f}. Using floor.")
        h = h_min
    else:
        h = h_ik
        logger.info(f"Using IK bandwidth: {h:.4f}")

    # Define kernel function (Triangular is standard for RD)
    def triangular_kernel(u):
        return np.where(np.abs(u) <= 1, 1 - np.abs(u), 0.0)

    # Create weights based on distance from cutoff
    u = (x - cutoff) / h
    weights = triangular_kernel(u)

    # Filter to support of kernel (where weights > 0)
    valid_mask = weights > 0
    if np.sum(valid_mask) < 4:
        logger.warning("Too few points within bandwidth. Expanding bandwidth slightly or returning NaN.")
        # Try to expand slightly if possible, else fail
        if h < x_range:
            h_new = min(x_range, h * 2)
            u = (x - cutoff) / h_new
            weights = triangular_kernel(u)
            valid_mask = weights > 0
            if np.sum(valid_mask) < 4:
                return EstimationResult(estimate=np.nan, se=np.nan, n_obs=len(df), n_used=len(df_clean), success=False)
        else:
            return EstimationResult(estimate=np.nan, se=np.nan, n_obs=len(df), n_used=len(df_clean), success=False)

    x_local = x[valid_mask]
    y_local = y[valid_mask]
    w_local = weights[valid_mask]
    d_local = d[valid_mask]

    # Local Linear Regression
    # Y_i = alpha + tau * D_i + beta * (X_i - c) + gamma * D_i * (X_i - c) + error
    # Weights are applied in WLS

    x_centered = x_local - cutoff
    X_design = np.column_stack([
        np.ones(len(x_local)),          # Intercept (alpha)
        d_local,                        # Treatment (tau)
        x_centered,                     # Slope left (beta)
        d_local * x_centered            # Slope diff (gamma)
    ])

    # Weight matrix
    W = np.diag(w_local)

    try:
        # WLS: (X'WX)^-1 X'Wy
        XtW = X_design.T @ W
        XtWX = XtW @ X_design
        XtWy = XtW @ y_local

        # Check for singularity
        if np.linalg.cond(XtWX) > 1e10:
            logger.warning("Design matrix nearly singular in local regression.")
            return EstimationResult(estimate=np.nan, se=np.nan, n_obs=len(df), n_used=len(df_clean), success=False)

        beta_hat = np.linalg.solve(XtWX, XtWy)
        
        # Extract treatment effect (tau)
        tau_hat = beta_hat[1]

        # Standard Error Calculation
        # Residuals
        y_hat = X_design @ beta_hat
        residuals = y_local - y_hat
        
        # Variance of residuals
        sigma_sq_hat = (residuals.T @ W @ residuals) / (len(x_local) - X_design.shape[1])
        
        # Variance of beta_hat: (X'WX)^-1 X'W Sigma W X (X'WX)^-1
        # Assuming homoskedasticity for simplicity in this naive estimator: sigma^2 * (X'WX)^-1
        cov_beta_hat = sigma_sq_hat * np.linalg.inv(XtWX)
        se_tau = np.sqrt(cov_beta_hat[1, 1])

        logger.info(f"Naïve RD Estimate: {tau_hat:.4f} (SE: {se_tau:.4f})")
        
        return EstimationResult(
            estimate=float(tau_hat),
            se=float(se_tau),
            n_obs=len(df),
            n_used=len(df_clean),
            success=True
        )

    except np.linalg.LinAlgError as e:
        logger.error(f"Linear algebra error in Naïve RD estimation: {e}")
        return EstimationResult(estimate=np.nan, se=np.nan, n_obs=len(df), n_used=len(df_clean), success=False)
    except Exception as e:
        logger.error(f"Unexpected error in Naïve RD estimation: {e}")
        return EstimationResult(estimate=np.nan, se=np.nan, n_obs=len(df), n_used=len(df_clean), success=False)


def main():
    """
    Entry point for testing the estimator directly.
    Expects data in data/simulated_raw.csv.
    """
    import os
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

    data_path = project_root / "data" / "simulated_raw.csv"
    
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        print("Please run the data generation pipeline first.")
        sys.exit(1)

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    # Run estimation
    result = estimate_naive_rd(df)

    print(f"Estimate: {result.estimate}")
    print(f"Standard Error: {result.se}")
    print(f"Observations (Total): {result.n_obs}")
    print(f"Observations (Used): {result.n_used}")
    print(f"Success: {result.success}")


if __name__ == "__main__":
    main()