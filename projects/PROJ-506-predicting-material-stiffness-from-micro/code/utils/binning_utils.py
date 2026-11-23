"""
Binning utilities for inclusion density stratification.

This module provides deterministic binning strategies to discretize continuous
inclusion density values into categorical labels for stratified sampling.
"""
from typing import List, Union
import numpy as np


def define_density_bins(density_values: Union[List[float], np.ndarray]) -> List[str]:
    """
    Discretize continuous inclusion density values into stratification bins.

    Uses a quantile-based strategy to ensure balanced distribution across bins,
    which is critical for effective StratifiedKFold cross-validation.

    Args:
        density_values: List or array of continuous inclusion density values
            (volume fraction of inclusions, typically 0.0 to 1.0).

    Returns:
        List of string labels corresponding to each input value, using:
            - 'low' for the lowest 33.3% of densities
            - 'med' for the middle 33.3%
            - 'high' for the top 33.3%

    Raises:
        ValueError: If input is empty or contains invalid values.
        TypeError: If input is not a list or numpy array.

    Note:
        This function is deterministic for the same input set. It uses
        numpy's percentile function with linear interpolation to define
        bin edges, ensuring consistent bin assignment across runs.
    """
    if not isinstance(density_values, (list, np.ndarray)):
        raise TypeError(f"Expected list or numpy array, got {type(density_values)}")

    arr = np.asarray(density_values, dtype=float)

    if arr.size == 0:
        raise ValueError("Input density_values cannot be empty")

    if np.any(np.isnan(arr)) or np.any(arr < 0) or np.any(arr > 1):
        raise ValueError(f"Density values must be in range [0, 1]. Got: min={arr.min()}, max={arr.max()}")

    # Define 3 quantile-based bins: low, med, high
    # Use 33.33 and 66.67 percentiles as boundaries
    percentile_33 = np.percentile(arr, 33.33)
    percentile_66 = np.percentile(arr, 66.67)

    labels = []
    for val in arr:
        if val <= percentile_33:
            labels.append('low')
        elif val <= percentile_66:
            labels.append('med')
        else:
            labels.append('high')

    return labels
