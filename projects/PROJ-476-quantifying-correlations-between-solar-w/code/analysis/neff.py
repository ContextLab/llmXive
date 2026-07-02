"""
Effective Sample Size (Neff) calculation module.

Implements the Pyper & Peterman method for calculating Neff using
lag-1 autocorrelation on detrended time series.
"""
import numpy as np
import pandas as pd
from scipy import signal
from code import logger

def calculate_neff(series: pd.Series) -> float:
    """
    Calculate the effective sample size (Neff) for a time series.

    Uses the formula: Neff = N * (1 - rho_1) / (1 + rho_1)
    where rho_1 is the lag-1 autocorrelation of the detrended series.

    Args:
        series: A pandas Series containing the time series data.

    Returns:
        The effective sample size (float).
    """
    if not isinstance(series, pd.Series):
        series = pd.Series(series)

    # Drop NaNs
    clean_series = series.dropna()
    n = len(clean_series)

    if n < 3:
        logger.warning(f"Series too short ({n}) to calculate Neff. Returning N.")
        return float(n)

    # Detrend the series (remove linear trend)
    # scipy.signal.detrend removes the mean and linear trend
    detrended = signal.detrend(clean_series.values)

    # Calculate lag-1 autocorrelation of the residuals
    # rho_1 = Cov(X_t, X_{t-1}) / Var(X_t)
    # Using numpy corrcoef on shifted arrays
    x = detrended[:-1]
    y = detrended[1:]

    if len(x) < 2:
        return float(n)

    # Avoid division by zero if variance is 0
    var_x = np.var(x)
    if var_x == 0:
        logger.warning("Variance of detrended series is zero. Returning N.")
        return float(n)

    # Correlation
    try:
        rho_1 = np.corrcoef(x, y)[0, 1]
    except Exception as e:
        logger.warning(f"Failed to calculate autocorrelation: {e}")
        return float(n)

    if np.isnan(rho_1):
        logger.warning("Autocorrelation is NaN. Returning N.")
        return float(n)

    # Clamp rho_1 to [-1, 1] to avoid numerical issues in formula
    rho_1 = np.clip(rho_1, -1.0, 1.0)

    # Pyper & Peterman formula
    # Neff = N * (1 - rho_1) / (1 + rho_1)
    if abs(1 + rho_1) < 1e-10:
        logger.warning("Denominator near zero in Neff formula. Returning N.")
        return float(n)

    neff = n * (1 - rho_1) / (1 + rho_1)

    # Ensure Neff is positive and at most N
    neff = max(1.0, min(neff, float(n)))

    return neff

def calculate_neff_for_subset(
    series: pd.Series,
    start_date: str,
    end_date: str
) -> float:
    """
    Calculate Neff for a specific subset of the time series.

    Args:
        series: The full time series.
        start_date: Start date string (e.g., '2018-01-01').
        end_date: End date string (e.g., '2020-12-31').

    Returns:
        The effective sample size for the subset.
    """
    # Filter by date
    mask = (series.index >= start_date) & (series.index <= end_date)
    subset = series[mask]

    return calculate_neff(subset)