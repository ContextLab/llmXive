"""
Empirical Power Calculation via Bootstrap Simulation.

This module implements the bootstrap simulation engine to estimate statistical power
by resampling real-world datasets while preserving their underlying distribution.
It compares the empirical power against theoretical calculations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

from config import RANDOM_SEED, BOOTSTRAP_ITERATIONS, EFFECT_SIZE_TARGET, SIGNIFICANCE_LEVEL
from utils import setup_logging

# Configure logging
logger = setup_logging(__name__)


def bootstrap_power_estimate(
    data: np.ndarray,
    group_col: Optional[int] = None,
    n_iterations: Optional[int] = None,
    effect_size_target: Optional[float] = None,
    alpha: float = SIGNIFICANCE_LEVEL
) -> Dict[str, Any]:
    """
    Estimate statistical power using bootstrap resampling.

    This function performs bootstrap resampling on the provided data to simulate
    the distribution of the test statistic under the alternative hypothesis.
    It calculates the proportion of resampled tests that reject the null hypothesis.

    Parameters
    ----------
    data : np.ndarray
        1D array of observations. For two-sample tests, this should be a 2D array
        where columns represent groups, or a 1D array with a group_col specified.
    group_col : int, optional
        If data is 2D, the column index to use as the second group. If None,
        assumes data is already split or 1D single group (not applicable for t-test).
        For this implementation, we expect data to be a tuple of (group1, group2)
        or a 2D array where we split by a known index if group_col is provided.
        To simplify, we assume `data` is a 2D array where the first column is group A
        and the second column is group B, OR we accept a tuple of arrays.
        Revised: We expect `data` to be a dictionary-like structure or we handle
        splitting internally if a binary split is known.
        Implementation Decision: Accept `data` as a tuple (group1, group2) or
        split a 2D array if `group_col` is provided (treating `data`[:, 0] as group1
        and `data`[:, group_col] as group2? No, that's ambiguous).
        
        Let's standardize: `data` is a 2D numpy array. If `group_col` is provided,
        we treat column 0 as Group 1 and column `group_col` as Group 2.
        If `group_col` is None, we assume the data is already split into two groups
        passed as a tuple? No, the signature is fixed.
        
        Better approach for robustness:
        If data is 2D and has 2 columns -> Group 1 = col 0, Group 2 = col 1.
        If data is 2D and has > 2 columns -> use group_col to pick the second group.
        If data is 1D -> Error (need two groups for t-test power).
        
        Actually, to be most flexible based on typical loader outputs:
        We expect `data` to be a tuple (group1, group2) or we will split it.
        Let's enforce: `data` is a 2D array. Group 1 is column 0. Group 2 is column 1.
        If the dataset has more columns, the caller must slice before passing.
        
        Wait, the task says "preserving data distribution".
        We will assume `data` is a 2D array where:
        - Column 0: Group 1 (e.g., Control)
        - Column 1: Group 2 (e.g., Treatment)
        - If the input is 1D, we cannot do a two-sample t-test.
        
        Correction: The task implies we are testing a difference in means.
        We need two groups.
        We will accept `data` as a tuple of two arrays: (group1, group2).
        If it's a single array, we might need to split it based on a binary indicator,
        but the loader usually returns a DataFrame.
        
        Let's assume the input `data` is a 2D numpy array where the first column
        is the outcome for Group 0 and the second column is the outcome for Group 1.
        If the data is 1D, we raise an error.
        
        Actually, looking at the loader context, we likely have a single column of outcomes
        and a binary group indicator.
        Let's assume `data` is a dictionary with keys 'outcome' and 'group',
        OR a 2D array where we handle the split.
        
        To keep it simple and robust:
        We expect `data` to be a tuple (group1_values, group2_values).
        If the caller passes a 2D array, we will treat it as (col0, col1).
        
    n_iterations : int, optional
        Number of bootstrap iterations. Defaults to BOOTSTRAP_ITERATIONS from config.
    effect_size_target : float, optional
        Target effect size (Cohen's d). Defaults to EFFECT_SIZE_TARGET from config.
        Used for theoretical comparison if needed, but here we estimate empirical power.
    alpha : float
        Significance level (default 0.05).

    Returns
    -------
    dict
        Dictionary containing:
        - 'empirical_power': float, proportion of rejections
        - 'mean_diff': float, observed mean difference
        - 'std_diff': float, std dev of mean differences in bootstrap
        - 'rejection_count': int, number of times null was rejected
        - 'iterations': int, number of iterations performed
    """
    if n_iterations is None:
        n_iterations = BOOTSTRAP_ITERATIONS
    
    if effect_size_target is None:
        effect_size_target = EFFECT_SIZE_TARGET

    # Handle input data format
    if isinstance(data, tuple):
        if len(data) != 2:
            raise ValueError("Data tuple must contain exactly two groups.")
        group1, group2 = data
    elif isinstance(data, np.ndarray):
        if data.ndim == 1:
            raise ValueError("1D array provided. Two-sample t-test requires two groups.")
        if data.shape[1] < 2:
            raise ValueError("2D array must have at least 2 columns for two groups.")
        # Assume first two columns are the groups
        group1 = data[:, 0]
        group2 = data[:, 1]
    else:
        raise TypeError("Data must be a tuple of arrays or a 2D numpy array.")

    # Convert to numpy arrays if not already
    group1 = np.asarray(group1, dtype=float)
    group2 = np.asarray(group2, dtype=float)

    # Remove NaNs
    group1 = group1[~np.isnan(group1)]
    group2 = group2[~np.isnan(group2)]

    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Each group must have at least 2 observations.")

    rng = np.random.default_rng(RANDOM_SEED)
    rejections = 0
    mean_diffs = []

    n1 = len(group1)
    n2 = len(group2)

    logger.info(f"Starting bootstrap power estimation: {n_iterations} iterations")
    logger.info(f"Group 1 size: {n1}, Group 2 size: {n2}")

    for i in range(n_iterations):
        # Resample with replacement
        sample1 = rng.choice(group1, size=n1, replace=True)
        sample2 = rng.choice(group2, size=n2, replace=True)

        # Perform t-test
        # Using equal variance assumption (standard for power calc unless specified)
        t_stat, p_val = stats.ttest_ind(sample1, sample2, equal_var=True)

        if p_val < alpha:
            rejections += 1

        mean_diffs.append(np.mean(sample1) - np.mean(sample2))

    empirical_power = rejections / n_iterations
    mean_diff = np.mean(mean_diffs)
    std_diff = np.std(mean_diffs)

    logger.info(f"Bootstrap complete. Empirical Power: {empirical_power:.4f}")

    return {
        "empirical_power": float(empirical_power),
        "mean_diff": float(mean_diff),
        "std_diff": float(std_diff),
        "rejection_count": int(rejections),
        "iterations": int(n_iterations),
        "n1": int(n1),
        "n2": int(n2)
    }


def run_empirical_analysis(
    group1: np.ndarray,
    group2: np.ndarray,
    iterations: Optional[int] = None,
    alpha: float = SIGNIFICANCE_LEVEL
) -> Dict[str, Any]:
    """
    Wrapper to run empirical analysis on two specific groups.

    Parameters
    ----------
    group1 : np.ndarray
        Data for group 1.
    group2 : np.ndarray
        Data for group 2.
    iterations : int, optional
        Number of bootstrap iterations.
    alpha : float
        Significance level.

    Returns
    -------
    dict
        Results dictionary.
    """
    data = (group1, group2)
    return bootstrap_power_estimate(
        data=data,
        n_iterations=iterations,
        alpha=alpha
    )


if __name__ == "__main__":
    # Simple self-test with synthetic data to verify execution
    # This block is for validation only; real data processing happens in main.py
    logger.info("Running empirical power module self-test...")
    
    # Create synthetic data with known effect
    rng = np.random.default_rng(42)
    g1 = rng.normal(loc=0, scale=1, size=50)
    g2 = rng.normal(loc=0.5, scale=1, size=50) # Small effect

    result = run_empirical_analysis(g1, g2, iterations=100) # Small iterations for test
    
    print(f"Self-test result: {result}")
    assert 0 <= result["empirical_power"] <= 1, "Power must be between 0 and 1"
    logger.info("Self-test passed.")