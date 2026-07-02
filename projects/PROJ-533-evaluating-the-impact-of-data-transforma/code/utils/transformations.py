"""
Transformation utilities for statistical analysis.

Implements Box-Cox, Yeo-Johnson, and rank-based inverse normal transformations.
Handles positive-value constraints and provides fallback strategies for invalid inputs.
"""
import numpy as np
from scipy import stats
from typing import Tuple, Optional, Union, List
import warnings

# Suppress specific scipy warnings during lambda optimization to keep logs clean
warnings.filterwarnings("ignore", category=RuntimeWarning, module="scipy.optimize")


def _validate_input(data: Union[np.ndarray, List[float]], name: str) -> np.ndarray:
    """Validate input data for transformation functions."""
    arr = np.asarray(data, dtype=float)
    if arr.size == 0:
        raise ValueError(f"{name}: Input array is empty.")
    if not np.isfinite(arr).all():
        raise ValueError(f"{name}: Input contains non-finite values (NaN or Inf).")
    return arr


def box_cox_transform(
    data: Union[np.ndarray, List[float]],
    lambda_val: Optional[float] = None
) -> Tuple[np.ndarray, float]:
    """
    Apply Box-Cox transformation.

    Box-Cox requires strictly positive data. If the data contains non-positive
    values, this function raises a ValueError. Use `safe_box_cox` for automatic
    shifting.

    Args:
        data: Input 1D array of positive values.
        lambda_val: Optional lambda parameter. If None, it is estimated.

    Returns:
        Tuple of (transformed_data, lambda_parameter).
    """
    arr = _validate_input(data, "Box-Cox")

    if np.any(arr <= 0):
        raise ValueError(
            "Box-Cox transformation requires strictly positive data. "
            "Use safe_box_cox for automatic log-shift handling."
        )

    if lambda_val is not None:
        # Apply transformation with fixed lambda
        if abs(lambda_val) < 1e-6:
            transformed = np.log(arr)
        else:
            transformed = (np.power(arr, lambda_val) - 1) / lambda_val
        return transformed, lambda_val

    # Estimate lambda
    transformed, lambda_est = stats.boxcox(arr)
    return transformed, lambda_est


def safe_box_cox(
    data: Union[np.ndarray, List[float]],
    shift_constant: Optional[float] = None
) -> Tuple[np.ndarray, float, Optional[float]]:
    """
    Apply Box-Cox with automatic handling for non-positive values.

    If the data contains non-positive values, a constant is added to make
    all values positive before transformation.

    Args:
        data: Input 1D array.
        shift_constant: If provided, this value is added to all data points.
                       If None, the minimum shift (min(arr) + epsilon) is calculated.

    Returns:
        Tuple of (transformed_data, lambda_parameter, applied_shift).
        applied_shift is None if no shift was needed.
    """
    arr = _validate_input(data, "Safe Box-Cox")
    min_val = np.min(arr)
    applied_shift = None

    if min_val <= 0:
        if shift_constant is None:
            # Shift to make minimum value 1e-6 (small positive epsilon)
            shift_constant = abs(min_val) + 1e-6
        else:
            # Ensure provided constant is sufficient
            if min_val + shift_constant <= 0:
                shift_constant = abs(min_val) + 1e-6

        arr_shifted = arr + shift_constant
        applied_shift = shift_constant
    else:
        arr_shifted = arr

    transformed, lambda_est = stats.boxcox(arr_shifted)
    return transformed, lambda_est, applied_shift


def yeo_johnson_transform(
    data: Union[np.ndarray, List[float]],
    lambda_val: Optional[float] = None
) -> Tuple[np.ndarray, float]:
    """
    Apply Yeo-Johnson transformation.

    Yeo-Johnson can handle positive, negative, and zero values.

    Args:
        data: Input 1D array.
        lambda_val: Optional lambda parameter. If None, it is estimated.

    Returns:
        Tuple of (transformed_data, lambda_parameter).
    """
    arr = _validate_input(data, "Yeo-Johnson")

    if lambda_val is not None:
        transformed = stats.yeojohnson(arr, lmbda=lambda_val)
        return transformed, lambda_val

    transformed, lambda_est = stats.yeojohnson(arr)
    return transformed, lambda_est


def rank_inverse_normal_transform(
    data: Union[np.ndarray, List[float]],
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Apply Rank-based Inverse Normal Transformation (RINT).

    This method replaces data values with their rank-based quantiles from
    a standard normal distribution. It is robust to outliers and non-normality.

    Args:
        data: Input 1D array.
        epsilon: Small constant to avoid infinite values at tails (0 < epsilon < 0.5).
                Default is 1e-6, scaling the rank fraction to (1+epsilon)/(N+2).

    Returns:
        Transformed 1D array.
    """
    arr = _validate_input(data, "Rank Inverse Normal")
    n = len(arr)

    # Calculate ranks (1-based)
    # Using scipy.stats.rankdata with 'average' method for ties
    ranks = stats.rankdata(arr, method='average')

    # Convert ranks to probabilities in (0, 1) range
    # Formula: (rank - 0.5) / n is common, but we use (rank + epsilon) / (n + 2*epsilon)
    # to avoid exactly 0 or 1 which map to +/- inf in norm.ppf.
    # A standard robust formula is (rank - 0.375) / (n + 0.25) (Blom's method)
    # or (rank - 0.5) / n.
    # Here we use a simple scaling to avoid boundaries:
    p = (ranks - 0.5) / n

    # Clamp probabilities to avoid exactly 0 or 1
    p = np.clip(p, epsilon, 1 - epsilon)

    # Inverse normal transformation
    transformed = stats.norm.ppf(p)

    return transformed


def apply_transformation(
    data: Union[np.ndarray, List[float]],
    method: str = "yeo_johnson"
) -> Tuple[np.ndarray, dict]:
    """
    Generic wrapper to apply a specified transformation.

    Args:
        data: Input 1D array.
        method: One of 'box_cox', 'safe_box_cox', 'yeo_johnson', 'rank_normal'.

    Returns:
        Tuple of (transformed_data, metadata_dict).
        metadata_dict contains 'method', 'lambda' (if applicable), and 'shift' (if applicable).
    """
    arr = _validate_input(data, "Apply Transformation")

    if method == "box_cox":
        try:
            transformed, lam = box_cox_transform(arr)
            return transformed, {"method": "box_cox", "lambda": lam, "shift": None}
        except ValueError:
            raise ValueError(
                "Box-Cox failed due to non-positive data. "
                "Consider using 'safe_box_cox' or 'yeo_johnson' instead."
            )

    elif method == "safe_box_cox":
        transformed, lam, shift = safe_box_cox(arr)
        return transformed, {"method": "safe_box_cox", "lambda": lam, "shift": shift}

    elif method == "yeo_johnson":
        transformed, lam = yeo_johnson_transform(arr)
        return transformed, {"method": "yeo_johnson", "lambda": lam, "shift": None}

    elif method == "rank_normal":
        transformed = rank_inverse_normal_transform(arr)
        return transformed, {"method": "rank_normal", "lambda": None, "shift": None}

    else:
        raise ValueError(f"Unknown transformation method: {method}")