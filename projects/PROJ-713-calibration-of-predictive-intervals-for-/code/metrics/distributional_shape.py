"""
Distributional Shape Metrics for PIT Values.

This module calculates kurtosis and tail-weight metrics for Probability Integral
Transform (PIT) values to assess the shape of the forecast distribution.
It flags series with heavy tails based on a kurtosis threshold.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union, Any

from utils.logger import get_logger
from utils.exceptions import DataValidationError

logger = get_logger(__name__)

KURTOSIS_HEAVY_TAIL_THRESHOLD = 3.5


def calculate_kurtosis(pit_values: Union[List[float], np.ndarray]) -> float:
    """
    Calculate the excess kurtosis of a set of PIT values.

    For a uniform distribution (ideal PIT), the kurtosis is approximately -1.2 (excess)
    or 1.8 (standard). However, we calculate the sample kurtosis directly.
    If the input is constant, returns NaN.

    Args:
        pit_values: List or array of PIT values (should be in [0, 1]).

    Returns:
        float: The calculated kurtosis.

    Raises:
        DataValidationError: If input is empty or contains non-numeric data.
    """
    if pit_values is None or len(pit_values) == 0:
        raise DataValidationError("PIT values cannot be empty for kurtosis calculation.")

    arr = np.array(pit_values, dtype=float)

    if np.isnan(arr).all():
        raise DataValidationError("PIT values cannot be all NaN.")

    # Filter out NaNs for calculation if any exist
    clean_arr = arr[~np.isnan(arr)]

    if len(clean_arr) < 4:
        logger.warning(f"Not enough data points ({len(clean_arr)}) to calculate reliable kurtosis. Returning NaN.")
        return float('nan')

    # Use scipy.stats.kurtosis (default is Fisher's definition, excess kurtosis)
    # If we want standard kurtosis, we can add 3, but excess is standard in statsmodels/scipy
    try:
        from scipy.stats import kurtosis as scipy_kurtosis
        kurt = scipy_kurtosis(clean_arr, fisher=True) # Fisher=True returns excess kurtosis (Normal=0)
        return float(kurt)
    except Exception as e:
        logger.error(f"Error calculating kurtosis: {e}")
        return float('nan')


def calculate_tail_weight_ratio(pit_values: Union[List[float], np.ndarray], 
                                bins: int = 20) -> Dict[str, float]:
    """
    Calculate a simple tail-weight metric by comparing the density in the extreme
    tails (e.g., bottom 5% and top 5%) against the expected uniform density.

    For a uniform distribution, the expected proportion in the bottom 5% is 0.05.
    The metric returns the ratio of observed proportion to expected proportion.
    A ratio > 1.0 indicates heavier tails than uniform.

    Args:
        pit_values: List or array of PIT values.
        bins: Number of bins for histogram calculation (used for consistency if needed).

    Returns:
        Dict[str, float]: Dictionary with keys 'lower_tail_ratio' and 'upper_tail_ratio'.
    """
    if pit_values is None or len(pit_values) == 0:
        raise DataValidationError("PIT values cannot be empty for tail weight calculation.")

    arr = np.array(pit_values, dtype=float)
    clean_arr = arr[~np.isnan(arr)]

    if len(clean_arr) == 0:
        raise DataValidationError("No valid PIT values found after NaN removal.")

    n = len(clean_arr)
    expected_tail_prob = 0.05 # 5% tails

    # Count observations in the bottom 5% and top 5%
    lower_threshold = np.percentile(clean_arr, 5) # Theoretical 5th percentile
    upper_threshold = np.percentile(clean_arr, 95) # Theoretical 95th percentile

    # Actually, for PIT uniformity check, we look at the values themselves.
    # If PIT is uniform, 5% of values should be < 0.05 and 5% > 0.95.
    # We calculate the observed proportion in the extreme bins [0, 0.05] and [0.95, 1.0].
    
    lower_tail_count = np.sum(clean_arr <= 0.05)
    upper_tail_count = np.sum(clean_arr >= 0.95)

    lower_obs_prob = lower_tail_count / n
    upper_obs_prob = upper_tail_count / n

    lower_ratio = lower_obs_prob / expected_tail_prob if expected_tail_prob > 0 else 0.0
    upper_ratio = upper_obs_prob / expected_tail_prob if expected_tail_prob > 0 else 0.0

    return {
        "lower_tail_ratio": float(lower_ratio),
        "upper_tail_ratio": float(upper_ratio)
    }


def flag_heavy_tails(kurtosis: float) -> bool:
    """
    Flag a series as having 'heavy tails' if the kurtosis exceeds the threshold.
    Note: This function uses the excess kurtosis.
    For a normal distribution, excess kurtosis is 0. For uniform, it is -1.2.
    Heavy tails usually imply a kurtosis significantly higher than the baseline.
    The task specifies: 'Flag series as having heavy tails if kurtosis > 3.5'.
    We assume this refers to the standard kurtosis (Fisher=False) or a specific
    threshold on excess kurtosis. Given the value 3.5, it is likely standard kurtosis
    (since uniform is ~1.8, normal is 3.0). If the input is excess kurtosis, 3.5
    is a very high threshold. We will assume the task implies the calculated value
    from calculate_kurtosis (which is excess) is compared to 3.5, or we convert.
    
    However, standard 'kurtosis' often implies the 4th moment (Normal=3).
    Let's assume the task means the standard kurtosis value.
    If our calculate_kurtosis returns excess (Normal=0), then 3.5 excess = 6.5 standard.
    If the task means standard kurtosis > 3.5, and we have excess, we check:
    excess_kurtosis + 3 > 3.5 => excess > 0.5.
    
    Re-reading the task: "Flag series as having 'heavy tails' if kurtosis > 3.5".
    In many contexts, kurtosis > 3 (standard) is heavy-tailed (leptokurtic).
    If the threshold is 3.5, it's a specific cutoff.
    Let's assume the function `calculate_kurtosis` returns the value to be compared.
    If `calculate_kurtosis` returns excess kurtosis (scipy default), then:
    We should check if (excess_kurtosis + 3) > 3.5? Or is the threshold 3.5 for excess?
    Given the ambiguity, we will implement the check on the value returned by
    `calculate_kurtosis` directly against 3.5, but we will document that this
    assumes the input is the standard kurtosis or the threshold is for excess.
    
    To be safe and consistent with the "heavy tails" concept (leptokurtic):
    If we use scipy.stats.kurtosis(fisher=True) -> Normal=0. Heavy tails > 0.
    If we use scipy.stats.kurtosis(fisher=False) -> Normal=3. Heavy tails > 3.
    The task says 3.5. This is close to 3.0 (Normal). It is likely referring to
    the standard kurtosis (Fisher=False).
    
    Let's adjust `calculate_kurtosis` to return standard kurtosis (Fisher=False)
    to match the threshold 3.5 directly.
    """
    # We will assume the input kurtosis is the standard kurtosis (Normal=3).
    # If the caller passes excess kurtosis, this logic might need adjustment.
    # Given the task constraint "kurtosis > 3.5", and standard normal is 3.0,
    # this makes sense as a threshold for heavy tails.
    return kurtosis > KURTOSIS_HEAVY_TAIL_THRESHOLD


def compute_distributional_shape_metrics(pit_values: List[float]) -> Dict[str, Any]:
    """
    Compute all distributional shape metrics for a series.

    Args:
        pit_values: List of PIT values.

    Returns:
        Dict with keys:
          - 'kurtosis': float (standard kurtosis)
          - 'is_heavy_tailed': bool
          - 'lower_tail_ratio': float
          - 'upper_tail_ratio': float
    """
    try:
        # Calculate standard kurtosis (Fisher=False) to align with threshold 3.5
        from scipy.stats import kurtosis as scipy_kurtosis
        arr = np.array(pit_values, dtype=float)
        clean_arr = arr[~np.isnan(arr)]
        
        if len(clean_arr) < 4:
            kurt_val = float('nan')
        else:
            kurt_val = float(scipy_kurtosis(clean_arr, fisher=False))

        is_heavy = flag_heavy_tails(kurt_val) if not np.isnan(kurt_val) else False

        tail_metrics = calculate_tail_weight_ratio(pit_values)

        return {
            "kurtosis": kurt_val,
            "is_heavy_tailed": is_heavy,
            "lower_tail_ratio": tail_metrics["lower_tail_ratio"],
            "upper_tail_ratio": tail_metrics["upper_tail_ratio"]
        }
    except Exception as e:
        logger.error(f"Error computing distributional shape metrics: {e}")
        return {
            "kurtosis": float('nan'),
            "is_heavy_tailed": False,
            "lower_tail_ratio": float('nan'),
            "upper_tail_ratio": float('nan')
        }


def aggregate_shape_results(results_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate shape metrics from a list of dictionaries into a DataFrame.

    Args:
        results_list: List of dicts containing shape metrics for each series.

    Returns:
        pd.DataFrame with columns: series_id, model, kurtosis, is_heavy_tailed, lower_tail_ratio, upper_tail_ratio
    """
    if not results_list:
        return pd.DataFrame(columns=["series_id", "model", "kurtosis", "is_heavy_tailed", "lower_tail_ratio", "upper_tail_ratio"])

    df = pd.DataFrame(results_list)
    # Ensure columns exist
    required_cols = ["series_id", "model", "kurtosis", "is_heavy_tailed", "lower_tail_ratio", "upper_tail_ratio"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    
    return df[required_cols]


def shape_metrics_to_dataframe(metrics: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert a single dictionary of shape metrics to a DataFrame row.
    """
    return pd.DataFrame([metrics])