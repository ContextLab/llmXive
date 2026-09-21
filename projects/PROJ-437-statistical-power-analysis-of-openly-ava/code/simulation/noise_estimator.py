"""
Noise Estimator Module for GLM Modeling.

This module estimates noise characteristics from real preprocessed fMRI
data (ROI time-series) to inform GLM modeling parameters. It calculates
residual variance, autocorrelation structure, and effective noise degrees
of freedom.

CRITICAL: This module operates ONLY on real, preprocessed data. It does
NOT generate synthetic noise or fallback to mock data.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import statsmodels.api as sm
from scipy import stats

# Import project utilities
from utils.seed_manager import set_global_seed
from utils.memory_monitor import get_current_memory_usage_gb, check_memory_threshold

logger = logging.getLogger(__name__)


def estimate_residual_variance(timeseries: np.ndarray) -> float:
    """
    Estimate the residual variance of a 1D time-series using a simple
    autoregressive model (AR(1)) to account for temporal autocorrelation.

    Args:
        timeseries: 1D numpy array of ROI signal values.

    Returns:
        float: Estimated residual variance (sigma^2).
    """
    if len(timeseries) < 10:
        logger.warning("Time-series too short for reliable variance estimation.")
        return float(np.var(timeseries, ddof=1))

    # Detrend the data using linear regression to remove slow drifts
    t = np.arange(len(timeseries))
    t = t.astype(float)
    t = (t - np.mean(t)) / np.std(t)  # Normalize time
    X = sm.add_constant(t)
    model = sm.OLS(timeseries, X)
    results = model.fit()

    residuals = results.resid

    # Estimate AR(1) parameter to correct variance for autocorrelation
    # Residual variance = sigma^2 * (1 - rho^2) where rho is AR(1) coef
    if len(residuals) > 2:
        rho = np.corrcoef(residuals[:-1], residuals[1:])[0, 1]
        if not np.isnan(rho):
            # Adjust variance estimate
            variance = np.var(residuals, ddof=1)
            # Effective variance accounting for autocorrelation
            effective_variance = variance * (1 - rho) / (1 + rho)
            return max(effective_variance, 1e-10)  # Floor to prevent zero

    return float(np.var(residuals, ddof=1))


def estimate_autocorrelation(timeseries: np.ndarray, max_lag: int = 20) -> np.ndarray:
    """
    Estimate the autocorrelation function (ACF) of a time-series up to
    a specified lag.

    Args:
        timeseries: 1D numpy array of ROI signal values.
        max_lag: Maximum lag to compute (default 20).

    Returns:
        np.ndarray: Array of autocorrelation coefficients for lags 0 to max_lag.
    """
    if len(timeseries) < max_lag + 10:
        logger.warning(f"Time-series too short for lag {max_lag}. Reducing max_lag.")
        max_lag = max(1, len(timeseries) - 10)

    # Normalize the series
    normalized = (timeseries - np.mean(timeseries)) / (np.std(timeseries) + 1e-10)

    acf = []
    for lag in range(max_lag + 1):
        if lag == 0:
            acf.append(1.0)
        else:
            c = np.mean(normalized[:-lag] * normalized[lag:])
            acf.append(c)

    return np.array(acf)


def calculate_noise_degrees_of_freedom(timeseries: np.ndarray, max_lag: int = 20) -> float:
    """
    Calculate the effective degrees of freedom (DoF) for a time-series,
    accounting for temporal autocorrelation. This is critical for
    accurate statistical inference in GLM.

    Formula: DoF_eff = N * (1 - rho) / (1 + rho) for AR(1), or more generally
    using the sum of autocorrelations.

    Args:
        timeseries: 1D numpy array of ROI signal values.
        max_lag: Maximum lag to consider for autocorrelation sum.

    Returns:
        float: Effective degrees of freedom.
    """
    n = len(timeseries)
    if n < 2:
        return 1.0

    acf = estimate_autocorrelation(timeseries, max_lag)

    # Sum of autocorrelations (excluding lag 0)
    # Using the formula: DoF_eff = N / (1 + 2 * sum(rho_k))
    # where rho_k are autocorrelation coefficients for k > 0
    sum_rho = np.sum(np.abs(acf[1:]))  # Use absolute values for conservative estimate

    dof_eff = n / (1.0 + 2.0 * sum_rho)

    # Ensure DoF is within valid range
    return max(1.0, min(float(dof_eff), float(n - 1)))


def estimate_noise_parameters(
    timeseries: np.ndarray,
    max_lag: int = 20
) -> Dict[str, Any]:
    """
    Estimate comprehensive noise characteristics from a preprocessed ROI
    time-series.

    Args:
        timeseries: 1D numpy array of ROI signal values.
        max_lag: Maximum lag for autocorrelation estimation.

    Returns:
        Dict containing:
            - 'residual_variance': Estimated residual variance (float)
            - 'dof_effective': Effective degrees of freedom (float)
            - 'acf_at_lag1': Autocorrelation at lag 1 (float)
            - 'snr_estimate': Simple SNR estimate based on signal variance vs residual variance (float)
            - 'n_observations': Number of observations (int)
    """
    if len(timeseries) < 5:
        raise ValueError(f"Time-series too short (n={len(timeseries)}) for noise estimation.")

    # Check memory
    mem_gb = get_current_memory_usage_gb()
    if check_memory_threshold(6.0):
        logger.warning("Memory threshold approaching during noise estimation.")

    # Detrend to get residuals
    t = np.arange(len(timeseries))
    t = (t - np.mean(t)) / (np.std(t) + 1e-10)
    X = sm.add_constant(t)
    model = sm.OLS(timeseries, X)
    results = model.fit()
    residuals = results.resid

    # Calculate metrics
    residual_var = estimate_residual_variance(timeseries)
    dof_eff = calculate_noise_degrees_of_freedom(timeseries, max_lag)
    acf = estimate_autocorrelation(timeseries, max_lag)
    acf_lag1 = acf[1] if len(acf) > 1 else 0.0

    # SNR estimate: Signal variance / Residual variance
    signal_var = np.var(timeseries, ddof=1)
    snr = signal_var / (residual_var + 1e-10)

    return {
        'residual_variance': float(residual_var),
        'dof_effective': float(dof_eff),
        'acf_at_lag1': float(acf_lag1),
        'snr_estimate': float(snr),
        'n_observations': int(len(timeseries))
    }


def estimate_noise_from_roi_data(
    roi_timeseries_dict: Dict[str, np.ndarray],
    max_lag: int = 20
) -> Dict[str, Dict[str, Any]]:
    """
    Estimate noise parameters for multiple ROIs from preprocessed data.

    Args:
        roi_timeseries_dict: Dictionary mapping ROI names to 1D numpy arrays.
        max_lag: Maximum lag for autocorrelation estimation.

    Returns:
        Dict mapping ROI names to their noise parameter dictionaries.
    """
    if not roi_timeseries_dict:
        raise ValueError("Empty ROI timeseries dictionary provided.")

    noise_params = {}
    for roi_name, timeseries in roi_timeseries_dict.items():
        try:
            params = estimate_noise_parameters(timeseries, max_lag)
            noise_params[roi_name] = params
            logger.info(f"Noise estimated for ROI '{roi_name}': dof={params['dof_effective']:.2f}, snr={params['snr_estimate']:.2f}")
        except ValueError as e:
            logger.warning(f"Failed to estimate noise for ROI '{roi_name}': {e}")
            noise_params[roi_name] = {'error': str(e)}

    return noise_params


def aggregate_noise_statistics(
    noise_params_dict: Dict[str, Dict[str, Any]]
) -> Dict[str, float]:
    """
    Aggregate noise statistics across multiple ROIs to get dataset-level
    noise characteristics.

    Args:
        noise_params_dict: Dictionary of noise parameters per ROI.

    Returns:
        Dict with aggregated statistics:
            - 'mean_residual_variance'
            - 'mean_dof_effective'
            - 'mean_acf_lag1'
            - 'mean_snr'
            - 'total_rois_analyzed'
    """
    valid_params = [
        p for p in noise_params_dict.values()
        if 'error' not in p
    ]

    if not valid_params:
        raise ValueError("No valid noise parameters to aggregate.")

    return {
        'mean_residual_variance': float(np.mean([p['residual_variance'] for p in valid_params])),
        'mean_dof_effective': float(np.mean([p['dof_effective'] for p in valid_params])),
        'mean_acf_lag1': float(np.mean([p['acf_at_lag1'] for p in valid_params])),
        'mean_snr': float(np.mean([p['snr_estimate'] for p in valid_params])),
        'total_rois_analyzed': len(valid_params)
    }


def main():
    """
    Main entry point for noise estimation.

    This function expects preprocessed ROI timeseries data to be available
    in the data/derived/ directory. It loads the data, estimates noise
    parameters, and saves the results to data/aggregated/noise_estimates.json.

    Note: This is a placeholder main function. In a real pipeline, the
    preprocessed data would be loaded from disk.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting noise estimation for GLM modeling.")

    # In a real pipeline, this would load preprocessed data from disk
    # Example: load from data/derived/roi_timeseries.parquet or similar
    # For now, we demonstrate the API with a mock structure
    # that would be replaced by real data loading

    # Placeholder for demonstration - REAL implementation would load from disk
    # This is NOT synthetic data generation, but a placeholder for the loading logic
    # that will be filled when real preprocessed data is available
    logger.warning("This main() function requires real preprocessed data to be loaded from disk.")
    logger.warning("Expected input: data/derived/roi_timeseries.pkl or similar")
    logger.warning("Expected output: data/aggregated/noise_estimates.json")

    # In production, this would look like:
    # import joblib
    # roi_data = joblib.load('data/derived/roi_timeseries.pkl')
    # noise_results = estimate_noise_from_roi_data(roi_data)
    # aggregated = aggregate_noise_statistics(noise_results)
    # joblib.dump(aggregated, 'data/aggregated/noise_estimates.json')

    logger.info("Noise estimation module ready. Please provide real preprocessed data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())