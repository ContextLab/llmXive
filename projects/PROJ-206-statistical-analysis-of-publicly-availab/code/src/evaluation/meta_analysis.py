"""
Meta-analysis module for statistical comparison of forecasting models.

Implements Diebold-Mariano (DM) tests with Westfall-Young correction
for pairwise comparison of forecast accuracy.

Sanctioned Architectural Exception:
This task implements the Spec's FR-006 DM test, overriding the Plan's
rejection of DM for static forecasts. This deviation is documented in
research.md as a hypothesis test for predictive accuracy.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Import from existing project modules
from src.utils.config import get_project_root, get_data_processed_path
from src.utils.logging import get_logger

logger = get_logger(__name__)

def diebold_mariano_test(
    actual: np.ndarray,
    forecast_a: np.ndarray,
    forecast_b: np.ndarray,
    loss_function: str = "squared",
    horizon: int = 1
) -> Tuple[float, float]:
    """
    Perform Diebold-Mariano test for equal predictive accuracy.

    The DM test evaluates whether the difference in loss between two
    forecasts is significantly different from zero.

    Args:
        actual: Array of actual values (e.g., election outcomes)
        forecast_a: Forecasts from model A
        forecast_b: Forecasts from model B
        loss_function: Loss function to use ("squared" or "absolute")
        horizon: Forecasting horizon (default 1 for point forecasts)

    Returns:
        Tuple of (DM statistic, p-value)
    """
    if len(actual) != len(forecast_a) or len(actual) != len(forecast_b):
        raise ValueError("Actual and forecasts must have the same length")

    if len(actual) < 10:
        logger.warning("Small sample size for DM test. Results may be unreliable.")

    # Calculate loss differential
    if loss_function == "squared":
        loss_a = (actual - forecast_a) ** 2
        loss_b = (actual - forecast_b) ** 2
    elif loss_function == "absolute":
        loss_a = np.abs(actual - forecast_a)
        loss_b = np.abs(actual - forecast_b)
    else:
        raise ValueError(f"Unknown loss function: {loss_function}")

    d = loss_a - loss_b

    # Calculate DM statistic
    n = len(d)
    mean_d = np.mean(d)

    # Autocovariance calculation for overlapping forecasts
    # Using Newey-West HAC estimator
    gamma_0 = np.var(d, ddof=1)
    gamma_sum = 0.0

    for h in range(1, horizon):
        if h < n:
            gamma_h = np.mean(d[:n-h] * d[h:])
            gamma_sum += 2 * gamma_h

    # Long-run variance estimate
    long_run_var = (gamma_0 + gamma_sum) / n

    if long_run_var <= 0:
        long_run_var = gamma_0 / n  # Fallback to simple variance

    dm_stat = mean_d / np.sqrt(long_run_var)

    # Two-sided p-value from standard normal
    p_value = 2 * (1 - stats.norm.cdf(abs(dm_stat)))

    return dm_stat, p_value

def westfall_young_stepdown_max_t(
    loss_diffs: List[np.ndarray],
    n_permutations: int = 1000,
    alpha: float = 0.05,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform Westfall-Young step-down max-t correction for multiple testing.

    This implements a permutation-based correction that controls the
    family-wise error rate (FWER) using a step-down max-t strategy.

    Args:
        loss_diffs: List of loss differential arrays (one per hypothesis test)
        n_permutations: Number of permutations for the correction
        alpha: Significance level
        seed: Random seed for reproducibility

    Returns:
        Tuple of (adjusted p-values, boolean array indicating rejection)
    """
    k = len(loss_diffs)
    if k == 0:
        return np.array([]), np.array([])

    if k == 1:
        # Single test: standard DM p-value
        dm_stat, p_val = diebold_mariano_test(
            np.zeros(len(loss_diffs[0])),  # Placeholder, actual DM uses forecasts
            np.zeros(len(loss_diffs[0])),
            np.zeros(len(loss_diffs[0]))
        )
        # We need to calculate actual DM statistics first
        pass

    n_obs = len(loss_diffs[0])
    rng = np.random.default_rng(seed)

    # Calculate original test statistics (t-statistics for each loss differential)
    original_t_stats = np.zeros(k)
    for i, d in enumerate(loss_diffs):
        mean_d = np.mean(d)
        std_d = np.std(d, ddof=1)
        if std_d > 0:
            original_t_stats[i] = mean_d / (std_d / np.sqrt(n_obs))
        else:
            original_t_stats[i] = 0.0

    # Sort original statistics in descending order for step-down
    sorted_indices = np.argsort(-original_t_stats)
    sorted_original_t = original_t_stats[sorted_indices]

    # Permutation matrix: max-t statistics from permutations
    max_t_stats = np.zeros(n_permutations)

    for perm in range(n_permutations):
        # Generate random signs for permutation
        signs = rng.choice([-1, 1], size=n_obs)

        # Calculate permuted test statistics for all hypotheses
        perm_t_stats = np.zeros(k)
        for i, d in enumerate(loss_diffs):
            d_perm = d * signs
            mean_d_perm = np.mean(d_perm)
            std_d_perm = np.std(d_perm, ddof=1)
            if std_d_perm > 0:
                perm_t_stats[i] = mean_d_perm / (std_d_perm / np.sqrt(n_obs))
            else:
                perm_t_stats[i] = 0.0

        # Store the maximum absolute t-statistic from this permutation
        max_t_stats[perm] = np.max(np.abs(perm_t_stats))

    # Calculate adjusted p-values using step-down max-t
    adjusted_p_values = np.ones(k)

    for i, idx in enumerate(sorted_indices):
        # Count how many permutations have max-t >= current observed t
        count = np.sum(max_t_stats >= np.abs(sorted_original_t[i]))
        p_adj = count / n_permutations

        # Step-down: ensure monotonicity (p-values should be non-decreasing in rank)
        if i > 0:
            p_adj = max(p_adj, adjusted_p_values[sorted_indices[i-1]])

        adjusted_p_values[idx] = min(p_adj, 1.0)

    # Determine rejections
    rejections = adjusted_p_values < alpha

    return adjusted_p_values, rejections

def run_pairwise_dm_tests(
    forecasts_df: pd.DataFrame,
    actual_outcomes: pd.Series,
    model_columns: List[str],
    n_permutations: int = 1000,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run pairwise Diebold-Mariano tests with Westfall-Young correction.

    Args:
        forecasts_df: DataFrame with forecast columns
        actual_outcomes: Series of actual election outcomes
        model_columns: List of column names containing forecasts
        n_permutations: Number of permutations for Westfall-Young
        alpha: Significance level

    Returns:
        Dictionary containing DM statistics, p-values, and adjusted results
    """
    if len(model_columns) < 2:
        logger.warning("Need at least 2 models for pairwise comparison")
        return {
            "dm_stats": {},
            "p_values": {},
            "adjusted_p_values": {},
            "rejections": {},
            "comparison_matrix": None
        }

    # Calculate loss differentials for all pairs
    loss_diffs_list = []
    pairs = []

    for i, model_a in enumerate(model_columns):
        for j, model_b in enumerate(model_columns):
            if i >= j:
                continue

            forecast_a = forecasts_df[model_a].values
            forecast_b = forecasts_df[model_b].values
            actual = actual_outcomes.values

            # Ensure same length
            min_len = min(len(actual), len(forecast_a), len(forecast_b))
            actual = actual[:min_len]
            forecast_a = forecast_a[:min_len]
            forecast_b = forecast_b[:min_len]

            # Calculate squared error losses
            loss_a = (actual - forecast_a) ** 2
            loss_b = (actual - forecast_b) ** 2
            loss_diff = loss_a - loss_b

            loss_diffs_list.append(loss_diff)
            pairs.append((model_a, model_b))

    if len(loss_diffs_list) == 0:
        return {
            "dm_stats": {},
            "p_values": {},
            "adjusted_p_values": {},
            "rejections": {},
            "comparison_matrix": None
        }

    # Run Westfall-Young correction
    adj_p_values, rejections = westfall_young_stepdown_max_t(
        loss_diffs_list,
        n_permutations=n_permutations,
        alpha=alpha
    )

    # Calculate individual DM statistics and p-values
    dm_stats = {}
    p_values = {}

    for idx, (model_a, model_b) in enumerate(pairs):
        forecast_a = forecasts_df[model_a].values
        forecast_b = forecasts_df[model_b].values
        actual = actual_outcomes.values

        min_len = min(len(actual), len(forecast_a), len(forecast_b))
        actual = actual[:min_len]
        forecast_a = forecast_a[:min_len]
        forecast_b = forecast_b[:min_len]

        dm_stat, p_val = diebold_mariano_test(actual, forecast_a, forecast_b)
        dm_stats[(model_a, model_b)] = dm_stat
        p_values[(model_a, model_b)] = p_val

    # Build comparison matrix
    comparison_matrix = pd.DataFrame(
        np.nan,
        index=model_columns,
        columns=model_columns
    )

    for idx, (model_a, model_b) in enumerate(pairs):
        comparison_matrix.loc[model_a, model_b] = adj_p_values[idx]
        comparison_matrix.loc[model_b, model_a] = adj_p_values[idx]

    return {
        "dm_stats": dm_stats,
        "p_values": p_values,
        "adjusted_p_values": dict(zip(pairs, adj_p_values)),
        "rejections": dict(zip(pairs, rejections)),
        "comparison_matrix": comparison_matrix
    }

def main():
    """
    Main entry point for meta-analysis.

    Loads processed forecasts and actual outcomes, performs pairwise
    Diebold-Mariano tests with Westfall-Young correction, and saves
    results to data/processed/meta_analysis_results.csv
    """
    project_root = get_project_root()
    data_path = get_data_processed_path()

    logger.info("Starting meta-analysis with Diebold-Mariano tests")

    # Load forecasts data
    try:
        forecasts_file = data_path / "frequentist_forecasts.csv"
        if not forecasts_file.exists():
            logger.error(f"Forecasts file not found: {forecasts_file}")
            return

        forecasts_df = pd.read_csv(forecasts_file)
        logger.info(f"Loaded forecasts from {forecasts_file}")
    except Exception as e:
        logger.error(f"Error loading forecasts: {e}")
        return

    # Load actual outcomes (should be in the same file or separate)
    # Assuming actual outcomes are in the harmonized data
    try:
        harmonized_file = data_path / "poll_data_cleaned.csv"
        if harmonized_file.exists():
            harmonized_df = pd.read_csv(harmonized_file)
            # Extract actual outcomes if available
            if "actual_outcome" in harmonized_df.columns:
                actual_outcomes = harmonized_df.set_index("date")["actual_outcome"]
            else:
                logger.warning("No actual outcomes found in harmonized data")
                return
        else:
            logger.warning("Harmonized data not found, attempting to use forecasts file")
            # Try to get actual from forecasts if available
            if "actual" in forecasts_df.columns:
                actual_outcomes = forecasts_df.set_index("date")["actual"]
            else:
                logger.error("Cannot find actual outcomes")
                return
    except Exception as e:
        logger.error(f"Error loading actual outcomes: {e}")
        return

    # Identify forecast columns
    forecast_cols = [col for col in forecasts_df.columns if "forecast" in col.lower()]

    if len(forecast_cols) < 2:
        logger.warning("Need at least 2 forecast columns for comparison")
        return

    # Run pairwise DM tests
    results = run_pairwise_dm_tests(
        forecasts_df,
        actual_outcomes,
        forecast_cols,
        n_permutations=1000,
        alpha=0.05
    )

    # Save results
    output_dir = data_path
    output_file = output_dir / "meta_analysis_results.csv"

    # Convert comparison matrix to CSV format
    if results["comparison_matrix"] is not None:
        results["comparison_matrix"].to_csv(output_file)
        logger.info(f"Saved meta-analysis results to {output_file}")

    # Log summary
    logger.info("Meta-analysis complete")
    logger.info(f"Number of pairwise comparisons: {len(results['dm_stats'])}")
    logger.info(f"Significant differences (alpha=0.05): {sum(results['rejections'].values())}")

    return results

if __name__ == "__main__":
    main()
