"""
Metrics module for calculating bias and error metrics in causal inference studies.
"""
from typing import Dict, Any, Union
import numpy as np
import pandas as pd

from .entities import CausalEstimate


def calculate_bias_metrics(
    estimates: Union[list[CausalEstimate], pd.DataFrame],
    ground_truth: float
) -> Dict[str, float]:
    """
    Calculate absolute bias and Root Mean Squared Error (RMSE) for a set of ATE estimates.

    This function implements FR-005 requirements for bias quantification.

    Args:
        estimates: A list of CausalEstimate objects or a DataFrame containing 'ate' column.
                   Each estimate represents an ATE calculation from a specific method/estimator.
        ground_truth: The known true ATE value (tau_true) from the data generation process.

    Returns:
        A dictionary containing:
            - 'absolute_bias': The mean absolute difference between estimates and ground truth.
            - 'rmse': The Root Mean Squared Error of the estimates.
            - 'mean_estimate': The mean of the provided estimates.
            - 'count': The number of estimates processed.

    Raises:
        ValueError: If estimates list is empty or if ground_truth is not a valid number.
        TypeError: If estimates input is not a list of CausalEstimate or a DataFrame.
    """
    if ground_truth is None or not isinstance(ground_truth, (int, float)):
        raise ValueError("ground_truth must be a valid numeric value.")

    # Extract ATE values from input
    ate_values = []

    if isinstance(estimates, pd.DataFrame):
        if 'ate' not in estimates.columns:
            raise ValueError("DataFrame must contain an 'ate' column.")
        ate_values = estimates['ate'].dropna().values
    elif isinstance(estimates, list):
        if not estimates:
            raise ValueError("Estimates list cannot be empty.")
        
        for est in estimates:
            if not isinstance(est, CausalEstimate):
                raise TypeError(f"Expected list of CausalEstimate, got {type(est)}")
            if est.ate is not None and not np.isnan(est.ate):
                ate_values.append(est.ate)
        ate_values = np.array(ate_values)
    else:
        raise TypeError("estimates must be a list of CausalEstimate or a pandas DataFrame.")

    if len(ate_values) == 0:
        raise ValueError("No valid ATE values found in estimates.")

    # Convert to numpy array for calculation
    ate_array = np.array(ate_values)

    # Calculate Absolute Bias (Mean Absolute Error)
    # Bias = E[estimate] - truth
    # Absolute Bias usually refers to Mean Absolute Error (MAE) in this context,
    # or the absolute value of the bias. We return MAE as the primary metric.
    absolute_bias = np.mean(np.abs(ate_array - ground_truth))

    # Calculate RMSE
    # RMSE = sqrt( mean( (estimate - truth)^2 ) )
    squared_errors = (ate_array - ground_truth) ** 2
    rmse = np.sqrt(np.mean(squared_errors))

    return {
        'absolute_bias': float(absolute_bias),
        'rmse': float(rmse),
        'mean_estimate': float(np.mean(ate_array)),
        'count': int(len(ate_array))
    }
