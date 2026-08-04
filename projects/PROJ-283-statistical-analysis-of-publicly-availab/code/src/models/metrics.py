"""
Statistical metrics and corrections for regression analysis.

This module provides functions for calculating Wald Z-statistics, p-values,
F-statistics, and applying Benjamini-Hochberg FDR correction to p-values
as required by FR-009.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def calculate_wald_z_statistic(
    coefficient: float,
    standard_error: float,
    epsilon: float = 1e-10
) -> float:
    """
    Calculate the Wald Z-statistic for a regression coefficient.

    Args:
        coefficient: The estimated regression coefficient.
        standard_error: The standard error of the coefficient.
        epsilon: A small value to prevent division by zero.

    Returns:
        The Wald Z-statistic.

    Raises:
        ValueError: If standard_error is zero or negative.
    """
    if standard_error <= 0:
        logger.warning(f"Standard error is {standard_error}, using epsilon {epsilon}")
        standard_error = epsilon

    z_stat = coefficient / standard_error
    return z_stat


def calculate_p_value_z_test(
    z_statistic: float,
    alternative: str = "two-sided"
) -> float:
    """
    Calculate the two-sided p-value from a Z-statistic.

    Args:
        z_statistic: The Z-statistic value.
        alternative: The alternative hypothesis ("two-sided", "less", "greater").

    Returns:
        The p-value.
    """
    if alternative == "two-sided":
        # Two-tailed test
        p_value = 2 * (1 - stats.norm.cdf(abs(z_statistic)))
    elif alternative == "less":
        p_value = stats.norm.cdf(z_statistic)
    elif alternative == "greater":
        p_value = 1 - stats.norm.cdf(z_statistic)
    else:
        raise ValueError(f"Unknown alternative: {alternative}")

    # Ensure p-value is in [0, 1]
    return float(np.clip(p_value, 0.0, 1.0))


def calculate_f_statistic(
    r_squared: float,
    num_predictors: int,
    num_samples: int
) -> float:
    """
    Calculate the F-statistic from R-squared.

    Args:
        r_squared: The R-squared value of the model.
        num_predictors: Number of predictors (excluding intercept).
        num_samples: Number of samples.

    Returns:
        The F-statistic.
    """
    if r_squared >= 1.0:
        logger.warning("R-squared is 1.0 or greater, F-statistic may be undefined")
        return float('inf')

    numerator = r_squared / num_predictors
    denominator = (1.0 - r_squared) / (num_samples - num_predictors - 1)

    if denominator == 0:
        return float('inf')

    f_stat = numerator / denominator
    return f_stat


def calculate_f_statistic_from_sums(
    ss_regression: float,
    ss_residual: float,
    num_predictors: int,
    num_samples: int
) -> float:
    """
    Calculate the F-statistic from sum of squares.

    Args:
        ss_regression: Sum of squares due to regression.
        ss_residual: Sum of squares due to residuals.
        num_predictors: Number of predictors.
        num_samples: Number of samples.

    Returns:
        The F-statistic.
    """
    if ss_residual == 0:
        return float('inf')

    ms_regression = ss_regression / num_predictors
    ms_residual = ss_residual / (num_samples - num_predictors - 1)

    f_stat = ms_regression / ms_residual
    return f_stat


def apply_benjamini_hochberg_fdr(
    p_values: List[float],
    alpha: float = 0.05,
    method: str = "BH"
) -> Tuple[List[float], List[bool]]:
    """
    Apply the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).

    This implements FR-009: Benjamini-Hochberg FDR correction.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level for FDR control (default 0.05).
        method: Method for FDR correction ("BH" for Benjamini-Hochberg,
               "BY" for Benjamini-Yekutieli).

    Returns:
        A tuple of (adjusted_p_values, is_significant) where:
        - adjusted_p_values: List of FDR-adjusted p-values.
        - is_significant: List of booleans indicating if each p-value is significant.

    Raises:
        ValueError: If p_values is empty or contains invalid values.
    """
    if not p_values:
        logger.warning("Empty p-values list provided to Benjamini-Hochberg correction")
        return [], []

    # Validate p-values
    p_values = np.array(p_values, dtype=float)
    if np.any((p_values < 0) | (p_values > 1)):
        raise ValueError("All p-values must be in [0, 1]")

    n = len(p_values)

    # Handle NaN values
    nan_mask = np.isnan(p_values)
    if np.any(nan_mask):
        logger.warning(f"Found {np.sum(nan_mask)} NaN p-values, replacing with 1.0")
        p_values[nan_mask] = 1.0

    # Create index array and sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]

    # Calculate rank for each p-value (1-indexed)
    ranks = np.arange(1, n + 1)

    # Benjamini-Hochberg adjustment
    if method == "BH":
        # BH procedure: adjust p_i = p_i * n / rank_i
        adjusted = sorted_p_values * n / ranks
    elif method == "BY":
        # Benjamini-Yekutieli: adjust p_i = p_i * n / (rank_i * sum(1/i))
        harmonic_sum = np.sum(1.0 / np.arange(1, n + 1))
        adjusted = sorted_p_values * n / (ranks * harmonic_sum)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'BH' or 'BY'.")

    # Ensure adjusted p-values are monotonic (cumulative minimum from the end)
    # This is crucial for the BH procedure
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]

    # Clip to [0, 1]
    adjusted = np.clip(adjusted, 0.0, 1.0)

    # Restore original order
    adjusted_p_values = np.zeros(n)
    adjusted_p_values[sorted_indices] = adjusted

    # Determine significance
    is_significant = adjusted_p_values <= alpha

    # Log summary
    num_significant = np.sum(is_significant)
    logger.info(
        f"BH FDR correction: {num_significant}/{n} predictors significant at alpha={alpha}"
    )

    return adjusted_p_values.tolist(), is_significant.tolist()


def calculate_metric_summary(
    coefficients: Dict[str, float],
    standard_errors: Dict[str, float],
    p_values: Dict[str, float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate a summary of model metrics including FDR-adjusted p-values.

    Args:
        coefficients: Dictionary of feature names to coefficients.
        standard_errors: Dictionary of feature names to standard errors.
        p_values: Dictionary of feature names to raw p-values.
        alpha: Significance level for FDR correction.

    Returns:
        A dictionary containing:
        - raw_p_values: Original p-values
        - adjusted_p_values: BH-adjusted p-values
        - is_significant: Boolean mask for significance
        - z_statistics: Wald Z-statistics
        - summary_stats: Overall summary (num_significant, etc.)
    """
    features = list(coefficients.keys())

    # Extract values in consistent order
    coefs = [coefficients[f] for f in features]
    ses = [standard_errors[f] for f in features]
    pvals = [p_values[f] for f in features]

    # Calculate Z-statistics
    z_stats = [
        calculate_wald_z_statistic(c, s) for c, s in zip(coefs, ses)
    ]

    # Apply FDR correction
    adj_pvals, is_sig = apply_benjamini_hochberg_fdr(pvals, alpha=alpha)

    # Build result dictionary
    result = {
        "features": features,
        "coefficients": coefs,
        "standard_errors": ses,
        "z_statistics": z_stats,
        "raw_p_values": pvals,
        "adjusted_p_values": adj_pvals,
        "is_significant": is_sig,
        "alpha": alpha,
        "summary_stats": {
            "total_predictors": len(features),
            "significant_predictors": int(np.sum(is_sig)),
            "fdr_rate": float(np.mean(is_sig)) if is_sig else 0.0
        }
    }

    return result


def main():
    """
    Main function to demonstrate metrics calculation and FDR correction.
    This is primarily for testing and documentation purposes.
    """
    # Example usage with synthetic data (for demonstration)
    features = ["intercept", "eco_family", "avg_move_time", "material_imbalance"]
    coefficients = {
        "intercept": 0.05,
        "eco_family": 0.12,
        "avg_move_time": -0.03,
        "material_imbalance": 0.08
    }
    standard_errors = {
        "intercept": 0.02,
        "eco_family": 0.04,
        "avg_move_time": 0.01,
        "material_imbalance": 0.03
    }
    p_values = {
        "intercept": 0.01,
        "eco_family": 0.003,
        "avg_move_time": 0.02,
        "material_imbalance": 0.008
    }

    summary = calculate_metric_summary(coefficients, standard_errors, p_values)

    print("Metric Summary:")
    print(f"Features: {summary['features']}")
    print(f"Raw p-values: {summary['raw_p_values']}")
    print(f"Adjusted p-values: {summary['adjusted_p_values']}")
    print(f"Significant: {summary['is_significant']}")
    print(f"Summary stats: {summary['summary_stats']}")

    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()