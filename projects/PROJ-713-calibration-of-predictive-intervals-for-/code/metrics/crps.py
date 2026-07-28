"""
Continuous Ranked Probability Score (CRPS) metrics module.

Calculates CRPS using properscoring.crps_ensemble to evaluate the
accuracy of probabilistic forecasts against observed values.
Supports both Gaussian (parametric) and Empirical CDF (sample-based) forecasts.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union, Any

from utils.logger import get_logger
from utils.exceptions import DataValidationError

logger = get_logger(__name__)

def compute_crps(
    forecasts: Union[np.ndarray, List[np.ndarray]],
    observations: Union[np.ndarray, List[float]],
    method: str = "ensemble",
    **kwargs
) -> Union[float, np.ndarray]:
    """
    Compute the Continuous Ranked Probability Score (CRPS).

    The CRPS measures the difference between the cumulative distribution
    function (CDF) of the predictive distribution and the CDF of the
    observed outcome (Heaviside step function). Lower values indicate better
    probabilistic calibration and sharpness.

    Args:
        forecasts:
            Predictive distributions. Can be:
            - np.ndarray of shape (n_samples, n_forecasts): If using empirical
              samples (e.g., from Monte Carlo or LSTM quantile simulations).
            - List[np.ndarray]: List of arrays where each element corresponds to
              the ensemble samples for a single forecast horizon.
            - For parametric (Gaussian) forecasts, pass a tuple (mean, std) or
              pre-processed ensemble if using 'ensemble' method.
        observations:
            Observed values. np.ndarray of shape (n_forecasts,) or list of floats.
        method:
            Calculation method. Currently supports "ensemble" which uses
            properscoring.crps_ensemble.
        **kwargs:
            Additional arguments passed to properscoring.crps_ensemble.
            - axis: Axis along which to compute CRPS (default 0 for ensemble samples).
            - weights: Optional weights for ensemble members.

    Returns:
        float or np.ndarray:
            - If single forecast or aggregated: float.
            - If multiple forecasts: np.ndarray of CRPS values per forecast.

    Raises:
        DataValidationError: If inputs are malformed, empty, or contain NaN/Inf.
        ImportError: If properscoring is not installed.
    """
    try:
        import properscoring
    except ImportError:
        logger.error("properscoring library is required but not installed.")
        raise ImportError(
            "The 'properscoring' package is required for CRPS calculation. "
            "Please install it via: pip install properscoring"
        )

    # Convert inputs to numpy arrays
    obs_array = np.asarray(observations, dtype=float)
    
    if obs_array.size == 0:
        raise DataValidationError("Observations array is empty.")
    
    if np.any(~np.isfinite(obs_array)):
        raise DataValidationError("Observations contain NaN or Inf values.")

    # Handle forecast input format
    if isinstance(forecasts, list):
        # Convert list of ensemble samples to 2D array
        # forecasts: List[np.ndarray] where each np.array is (n_samples,)
        if not forecasts:
            raise DataValidationError("Forecasts list is empty.")
        
        # Ensure all forecast arrays have the same number of samples
        sample_counts = [len(f) for f in forecasts]
        if len(set(sample_counts)) > 1:
            # Pad or truncate? For now, strict check or handle per horizon
            # Properscoring usually expects a single 2D array for batched processing
            # We will stack them if they align, otherwise compute individually
            logger.warning("Forecasts have varying ensemble sizes. Computing CRPS per horizon.")
            crps_values = []
            for i, (f, o) in enumerate(zip(forecasts, obs_array)):
                f_arr = np.asarray(f, dtype=float)
                if np.any(~np.isfinite(f_arr)):
                    raise DataValidationError(f"Forecast {i} contains NaN/Inf.")
                crps_val = properscoring.crps_ensemble(obs_array[i], f_arr)
                crps_values.append(crps_val)
            return np.array(crps_values)
        
        # Uniform size: stack into (n_forecasts, n_samples)
        # Note: properscoring expects (n_observations, n_members) or similar depending on axis
        # We will reshape to (n_forecasts, n_samples)
        try:
            forecast_array = np.vstack(forecasts).T  # Shape: (n_forecasts, n_samples)
        except ValueError as e:
            raise DataValidationError(f"Could not stack forecasts: {e}")
    else:
        forecast_array = np.asarray(forecasts, dtype=float)
        if forecast_array.ndim == 1:
            # If 1D, assume it's a single forecast ensemble or a single value
            # If it's a single value, CRPS is just absolute error? 
            # No, CRPS requires a distribution. If 1D is passed, treat as (n_forecasts,)
            # and assume deterministic? No, CRPS needs distribution.
            # Let's assume if 1D, it's already (n_samples,) for a single point?
            # Or (n_forecasts,) where we treat as deterministic (CRPS = |f - o|)?
            # Standard usage: 2D array (n_observations, n_ensemble_members)
            if forecast_array.shape[0] == len(obs_array):
                # Assume deterministic forecast? CRPS reduces to absolute error.
                # But strictly, CRPS is for probabilistic.
                # Let's assume the user passed (n_samples,) for a single forecast if len matches 1
                # This is ambiguous. Let's enforce 2D for batch or 1D for single.
                if len(obs_array) == 1:
                    forecast_array = forecast_array.reshape(1, -1)
                else:
                    raise DataValidationError(
                        "Forecast array is 1D but observations are multiple. "
                        "Provide 2D array (n_forecasts, n_samples) or list of arrays."
                    )
            else:
                # Assume (n_samples,) for a single forecast against multiple obs? Unlikely.
                # Assume (n_forecasts,) deterministic.
                # CRPS for deterministic forecast F is |F - Y|.
                # But properscoring expects ensemble.
                # We will treat 1D as (n_forecasts,) deterministic and compute abs diff.
                logger.warning("Detected 1D forecast array. Treating as deterministic forecasts. CRPS = |F - Y|.")
                return np.abs(forecast_array - obs_array)
    
    # Validate forecast array
    if forecast_array.shape[0] != len(obs_array):
        raise DataValidationError(
            f"Forecast array shape {forecast_array.shape} mismatch with observations {len(obs_array)}."
        )
    
    if np.any(~np.isfinite(forecast_array)):
        raise DataValidationError("Forecast array contains NaN or Inf values.")

    # Calculate CRPS
    # properscoring.crps_ensemble(observation, ensemble, axis=0, weights=None)
    # If forecast_array is (n_forecasts, n_samples), we need to pass it correctly.
    # Usually, we iterate or vectorize.
    # properscoring handles 1D obs and 2D ensemble (n_obs, n_members) if axis=1?
    # Let's check docs: crps_ensemble(observation, ensemble, axis=0)
    # If observation is scalar, ensemble is 1D.
    # If observation is 1D, ensemble is 2D (n_obs, n_members).
    
    # Our forecast_array is (n_forecasts, n_samples).
    # obs_array is (n_forecasts,).
    # We can pass them directly if we set axis=1 (members are along axis 1).
    
    try:
        crps_result = properscoring.crps_ensemble(
            obs_array, 
            forecast_array, 
            axis=1, 
            **kwargs
        )
    except Exception as e:
        logger.error(f"Error calculating CRPS: {e}")
        raise DataValidationError(f"CRPS calculation failed: {e}")

    if np.any(~np.isfinite(crps_result)):
        logger.warning("CRPS calculation resulted in non-finite values. Replacing with NaN.")
        crps_result = np.nan_to_num(crps_result, nan=np.nan)

    return crps_result


def aggregate_crps_results(
    crps_values: np.ndarray,
    model_name: str,
    dataset_name: str
) -> Dict[str, Any]:
    """
    Aggregate CRPS values into summary statistics.

    Args:
        crps_values: 1D array of CRPS scores per forecast.
        model_name: Name of the model used.
        dataset_name: Name of the dataset used.

    Returns:
        Dictionary containing mean, std, min, max, and count of CRPS values.
    """
    if len(crps_values) == 0:
        return {
            "model": model_name,
            "dataset": dataset_name,
            "mean_crps": np.nan,
            "std_crps": np.nan,
            "min_crps": np.nan,
            "max_crps": np.nan,
            "count": 0
        }

    # Filter NaNs for statistics
    valid_values = crps_values[np.isfinite(crps_values)]
    
    if len(valid_values) == 0:
        return {
            "model": model_name,
            "dataset": dataset_name,
            "mean_crps": np.nan,
            "std_crps": np.nan,
            "min_crps": np.nan,
            "max_crps": np.nan,
            "count": 0
        }

    return {
        "model": model_name,
        "dataset": dataset_name,
        "mean_crps": float(np.mean(valid_values)),
        "std_crps": float(np.std(valid_values)),
        "min_crps": float(np.min(valid_values)),
        "max_crps": float(np.max(valid_values)),
        "count": len(valid_values)
    }


def crps_to_dataframe(
    results: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Convert a list of aggregated CRPS result dictionaries to a DataFrame.

    Args:
        results: List of dicts from aggregate_crps_results.

    Returns:
        pandas DataFrame with CRPS metrics.
    """
    if not results:
        return pd.DataFrame()
    
    return pd.DataFrame(results)


def compute_crps_for_series(
    forecasts: Union[np.ndarray, List[np.ndarray]],
    observations: np.ndarray,
    model_name: str,
    series_id: str
) -> Dict[str, Any]:
    """
    Compute CRPS for a single time series and return structured results.

    Args:
        forecasts: Predictive distribution samples (ensemble).
        observations: Actual observed values.
        model_name: Name of the forecasting model.
        series_id: Identifier for the time series.

    Returns:
        Dictionary with series-level CRPS metrics.
    """
    try:
        crps_scores = compute_crps(forecasts, observations)
        
        # Ensure crps_scores is an array
        if np.isscalar(crps_scores):
            crps_scores = np.array([crps_scores])
        
        # Aggregate
        stats = aggregate_crps_results(crps_scores, model_name, series_id)
        stats["series_id"] = series_id
        stats["model"] = model_name
        
        return stats
    
    except DataValidationError as e:
        logger.warning(f"CRPS computation failed for series {series_id}: {e}")
        return {
            "series_id": series_id,
            "model": model_name,
            "mean_crps": np.nan,
            "std_crps": np.nan,
            "min_crps": np.nan,
            "max_crps": np.nan,
            "count": 0,
            "error": str(e)
        }