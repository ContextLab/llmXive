"""
apply_transformations.py

Skeleton implementation for applying Box-Cox, Yeo-Johnson, and Rank-based
transformations to datasets. Prepares for T022 full implementation.

This module provides function signatures and basic structure for:
- Box-Cox transformation (with log-shift intervention for negative values)
- Yeo-Johnson transformation (handles negative values natively)
- Rank-based inverse normal transformation

Dependencies:
- T006b (data_model): Dataset, Transformation, TestResult classes
- T009 (logging_config): JSON logger setup and intervention logging
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
from scipy import stats

# Import project utilities
from code.utils.data_model import Dataset, Transformation, TestResult
from code.utils.logging_config import (
    setup_pipeline_logger,
    log_transformation_intervention
)

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def box_cox_transform(data: np.ndarray, lmbda: Optional[float] = None) -> Tuple[np.ndarray, float]:
    """
    Apply Box-Cox transformation to the data.

    Box-Cox transformation is defined as:
    y(λ) = (x^λ - 1) / λ if λ != 0
    y(λ) = log(x) if λ = 0

    Note: Box-Cox requires strictly positive data. For negative or zero values,
    a log-shift intervention should be applied before calling this function.

    Args:
        data: 1D numpy array of strictly positive values
        lmbda: Optional lambda parameter. If None, optimal lambda is estimated.

    Returns:
        Tuple of (transformed_data, lambda_parameter)
    """
    if np.any(data <= 0):
        raise ValueError("Box-Cox transformation requires strictly positive data. "
                         "Consider applying log-shift intervention first.")

    if lmbda is None:
        transformed_data, lmbda = stats.boxcox(data)
    else:
        transformed_data = stats.boxcox(data, lmbda=lmbda)
        # Ensure we return a float for lmbda if it was provided
        if isinstance(lmbda, np.ndarray):
            lmbda = float(lmbda[0]) if len(lmbda) > 0 else 0.0
        else:
            lmbda = float(lmbda)

    return transformed_data, lmbda


def safe_box_cox(data: np.ndarray, logger: Optional[logging.Logger] = None) -> Tuple[np.ndarray, float, Dict[str, Any]]:
    """
    Apply Box-Cox transformation with safety checks and log-shift intervention.

    If data contains non-positive values, applies a log-shift (adding a constant
    to make all values positive) before transformation.

    Args:
        data: 1D numpy array (may contain negative or zero values)
        logger: Optional logger for recording interventions

    Returns:
        Tuple of (transformed_data, lambda_parameter, intervention_log)
        intervention_log contains details about any shifts applied
    """
    intervention_log = {
        "applied_shift": False,
        "shift_value": 0.0,
        "reason": "",
        "original_min": float(np.min(data))
    }

    if np.any(data <= 0):
        min_val = np.min(data)
        shift_value = abs(min_val) + 1.0  # Add 1 to ensure strictly positive
        shifted_data = data + shift_value

        intervention_log["applied_shift"] = True
        intervention_log["shift_value"] = float(shift_value)
        intervention_log["reason"] = f"Data contains non-positive values (min={min_val}). " \
                                    f"Applied log-shift of {shift_value:.4f}."

        if logger:
            log_transformation_intervention(
                logger,
                "box_cox_log_shift",
                intervention_log
            )

        transformed_data, lmbda = box_cox_transform(shifted_data)
    else:
        transformed_data, lmbda = box_cox_transform(data)

    return transformed_data, lmbda, intervention_log


def yeo_johnson_transform(data: np.ndarray, lmbda: Optional[float] = None) -> Tuple[np.ndarray, float]:
    """
    Apply Yeo-Johnson transformation to the data.

    Yeo-Johnson is an extension of Box-Cox that can handle zero and negative values.
    The transformation is:
    For x >= 0:
      y(λ) = ((x + 1)^λ - 1) / λ if λ != 0
      y(λ) = log(x + 1) if λ = 0
    For x < 0:
      y(λ) = -((-x + 1)^(2-λ) - 1) / (2-λ) if λ != 2
      y(λ) = -log(-x + 1) if λ = 2

    Args:
        data: 1D numpy array (can contain any real values)
        lmbda: Optional lambda parameter. If None, optimal lambda is estimated.

    Returns:
        Tuple of (transformed_data, lambda_parameter)
    """
    if lmbda is None:
        transformed_data, lmbda = stats.yeojohnson(data)
    else:
        transformed_data = stats.yeojohnson(data, lmbda=lmbda)
        if isinstance(lmbda, np.ndarray):
            lmbda = float(lmbda[0]) if len(lmbda) > 0 else 0.0
        else:
            lmbda = float(lmbda)

    return transformed_data, lmbda


def rank_inverse_normal_transform(data: np.ndarray) -> np.ndarray:
    """
    Apply rank-based inverse normal transformation (van der Waerden).

    This method replaces each value with its rank, then transforms the rank
    to a quantile of the standard normal distribution.

    Steps:
    1. Compute ranks of the data (handling ties by averaging)
    2. Convert ranks to percentiles: (rank - 0.5) / n
    3. Apply inverse normal CDF (probit) to get transformed values

    This transformation is robust to outliers and does not assume a specific
    distribution shape.

    Args:
        data: 1D numpy array of any real values

    Returns:
        Transformed numpy array with approximately normal distribution
    """
    n = len(data)
    if n == 0:
        return np.array([])

    # Compute ranks (average ranks for ties)
    ranks = stats.rankdata(data, method='average')

    # Convert ranks to percentiles (avoiding 0 and 1 to prevent infinite values)
    # Using (rank - 0.5) / n ensures values in (0, 1)
    percentiles = (ranks - 0.5) / n

    # Apply inverse normal CDF
    transformed_data = stats.norm.ppf(percentiles)

    return transformed_data


def apply_transformation(
    data: np.ndarray,
    method: str,
    lmbda: Optional[float] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply a specified transformation method to the data.

    Supported methods:
    - 'box_cox': Box-Cox transformation (with log-shift if needed)
    - 'yeo_johnson': Yeo-Johnson transformation
    - 'rank_normal': Rank-based inverse normal transformation

    Args:
        data: 1D numpy array to transform
        method: Transformation method ('box_cox', 'yeo_johnson', 'rank_normal')
        lmbda: Optional lambda parameter (only for Box-Cox and Yeo-Johnson)
        logger: Optional logger for recording interventions

    Returns:
        Tuple of (transformed_data, metadata_dict)
        metadata_dict contains: method, lambda_used, success, intervention_log
    """
    metadata = {
        "method": method,
        "lambda_used": lmbda,
        "success": False,
        "intervention_log": {}
    }

    try:
        if method == 'box_cox':
            transformed_data, lmbda_used, intervention_log = safe_box_cox(data, logger)
            metadata["lambda_used"] = lmbda_used
            metadata["intervention_log"] = intervention_log

        elif method == 'yeo_johnson':
            transformed_data, lmbda_used = yeo_johnson_transform(data, lmbda)
            metadata["lambda_used"] = lmbda_used

        elif method == 'rank_normal':
            transformed_data = rank_inverse_normal_transform(data)
            metadata["lambda_used"] = None  # No lambda for rank transformation

        else:
            raise ValueError(f"Unknown transformation method: {method}")

        metadata["success"] = True

    except Exception as e:
        if logger:
            logger.error(f"Transformation {method} failed: {str(e)}")
        metadata["error"] = str(e)
        transformed_data = data  # Return original data on failure

    return transformed_data, metadata


def transform_to_normality(
    data: np.ndarray,
    method: str = 'auto',
    logger: Optional[logging.Logger] = None
) -> Tuple[np.ndarray, str, Dict[str, Any]]:
    """
    Automatically select and apply the best transformation to achieve normality.

    If method is 'auto', tries Box-Cox first, then Yeo-Johnson, then rank-normal.
    Selects the method that produces the highest Shapiro-Wilk p-value (closest to normal).

    Args:
        data: 1D numpy array to transform
        method: 'auto', 'box_cox', 'yeo_johnson', or 'rank_normal'
        logger: Optional logger

    Returns:
        Tuple of (transformed_data, method_used, metadata)
    """
    if method != 'auto':
        transformed_data, metadata = apply_transformation(data, method, logger=logger)
        return transformed_data, method, metadata

    # Auto-selection: try all methods and pick the best
    methods_to_try = ['box_cox', 'yeo_johnson', 'rank_normal']
    best_method = None
    best_p_value = -1
    best_transformed = None
    best_metadata = None

    for m in methods_to_try:
        try:
            transformed, meta = apply_transformation(data, m, logger=logger)
            if meta["success"]:
                # Test normality of transformed data
                _, p_value = stats.shapiro(transformed)
                if p_value > best_p_value:
                    best_p_value = p_value
                    best_method = m
                    best_transformed = transformed
                    best_metadata = meta
        except Exception:
            continue

    if best_method is None:
        # Fallback to rank-normal if all else fails
        best_transformed, best_metadata = apply_transformation(data, 'rank_normal', logger=logger)
        best_method = 'rank_normal'

    return best_transformed, best_method, best_metadata


def main():
    """
    Main entry point for the transformations module.
    This is a skeleton function preparing for T022 implementation.
    """
    print("apply_transformations.py - Skeleton implementation")
    print("Ready for T022: Full implementation of Box-Cox, Yeo-Johnson, and Rank-based transformations")

    # Example usage (commented out for skeleton)
    # logger = setup_pipeline_logger()
    # sample_data = np.random.lognormal(0, 1, 100)
    # transformed, meta = apply_transformation(sample_data, 'box_cox', logger=logger)
    # print(f"Transformation successful: {meta['success']}")


if __name__ == "__main__":
    main()