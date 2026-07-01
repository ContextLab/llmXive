"""
Analysis module for aggregating simulation results and computing error rates.

This module provides functions to compute empirical Type I error rates and
their confidence intervals using the Clopper-Pearson (Exact) method.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Union
from scipy.stats import beta


def _clopper_pearson_interval(successes: int, n: int, alpha: float = 0.05) -> tuple:
    """
    Compute the Clopper-Pearson (Exact) confidence interval for a binomial proportion.

    Parameters
    ----------
    successes : int
        Number of successes (e.g., rejections of null hypothesis).
    n : int
        Total number of trials (e.g., total simulations).
    alpha : float
        Significance level for the confidence interval (default 0.05 for 95% CI).

    Returns
    -------
    tuple
        (lower_bound, upper_bound) of the confidence interval.
    """
    if n == 0:
        return 0.0, 0.0

    if successes == 0:
        lower = 0.0
    else:
        lower = beta.ppf(alpha / 2, successes, n - successes + 1)

    if successes == n:
        upper = 1.0
    else:
        upper = beta.ppf(1 - alpha / 2, successes + 1, n - successes)

    return lower, upper


def aggregate_errors(results_list: List[Dict], alpha_levels: List[float]) -> pd.DataFrame:
    """
    Aggregate simulation results to compute empirical Type I error rates and 95% CIs.

    This function processes a list of simulation result dictionaries (typically from
    `run_baseline_simulation` or `run_robust_simulation`) and calculates the proportion
    of times the null hypothesis was rejected at each specified alpha level for each
    method and ICC level. It uses the Clopper-Pearson exact method to compute
    confidence intervals for these rates.

    Parameters
    ----------
    results_list : List[Dict]
        List of dictionaries containing simulation results. Each dict should have
        at least 'p_value', 'icc', and 'method' keys.
    alpha_levels : List[float]
        List of significance levels (e.g., [0.01, 0.05, 0.10]) to evaluate.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - 'method': The statistical method used (e.g., 'naive', 'cluster_robust', 'block_permutation')
        - 'icc': The ICC value used in the simulation
        - 'alpha': The significance level
        - 'error_rate': Empirical Type I error rate (rejections / total_trials)
        - 'ci_lower': Lower bound of 95% CI (Clopper-Pearson)
        - 'ci_upper': Upper bound of 95% CI (Clopper-Pearson)
    """
    if not results_list:
        raise ValueError("results_list cannot be empty")

    # Verify required keys exist
    required_keys = {'p_value', 'icc', 'method'}
    if not required_keys.issubset(results_list[0].keys()):
        missing = required_keys - results_list[0].keys()
        raise ValueError(f"Results dictionaries must contain keys: {missing}")

    # Group by method and ICC
    methods = sorted(set(r['method'] for r in results_list))
    icc_values = sorted(set(r['icc'] for r in results_list))

    records = []

    for method in methods:
        for icc in icc_values:
            # Filter results for this method and ICC
            subset = [r for r in results_list if r['method'] == method and r['icc'] == icc]
            n_total = len(subset)

            if n_total == 0:
                continue

            for alpha in alpha_levels:
                # Count rejections (p-value < alpha)
                rejections = sum(1 for r in subset if r['p_value'] < alpha)

                # Compute error rate
                error_rate = rejections / n_total

                # Compute Clopper-Pearson confidence interval
                ci_lower, ci_upper = _clopper_pearson_interval(rejections, n_total, alpha=0.05)

                records.append({
                    'method': method,
                    'icc': icc,
                    'alpha': alpha,
                    'error_rate': error_rate,
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper
                })

    return pd.DataFrame(records)


def select_ci_method(error_rate: float, n: int) -> str:
    """
    Select the confidence interval method for the given parameters.

    This function always returns 'clopper_pearson' for this project to ensure
    statistical rigor and consistency with the Single Source of Truth principle.

    Parameters
    ----------
    error_rate : float
        The empirical error rate (not used in selection, but required for interface).
    n : int
        The number of trials (not used in selection, but required for interface).

    Returns
    -------
    str
        The string 'clopper_pearson'.
    """
    return 'clopper_pearson'