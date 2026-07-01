"""
Analysis module for computing Type I error rates and confidence intervals.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any

def select_ci_method(error_rate, n):
    """
    Select the confidence interval method for binomial proportions.

    For this project, we always use the Clopper-Pearson (Exact) method
    to ensure statistical rigor and consistency.

    Args:
        error_rate: Observed error rate (unused, but kept for API consistency)
        n: Number of trials (unused, but kept for API consistency)

    Returns:
        str: 'clopper_pearson'
    """
    return 'clopper_pearson'

def aggregate_errors(results_list: List[Dict[str, Any]], alpha_levels: List[float]) -> pd.DataFrame:
    """
    Aggregate simulation results to compute empirical Type I error rates
    and 95% confidence intervals using the Clopper-Pearson (Exact) method.

    Args:
        results_list: List of dictionaries containing simulation results.
                    Each dict should have keys: 'icc', 'p_value', 'iteration'
        alpha_levels: List of alpha levels to evaluate (e.g., [0.01, 0.05, 0.10])

    Returns:
        pd.DataFrame: DataFrame with columns:
                    - icc: Intra-cluster correlation value
                    - alpha: Significance level
                    - error_rate: Empirical Type I error rate
                    - ci_lower: Lower bound of 95% CI
                    - ci_upper: Upper bound of 95% CI
    """
    if not results_list:
        return pd.DataFrame(columns=['icc', 'alpha', 'error_rate', 'ci_lower', 'ci_upper'])

    # Extract unique ICC values
    icc_values = sorted(list(set(r['icc'] for r in results_list)))

    results = []

    for icc in icc_values:
        # Filter results for this ICC
        icc_results = [r for r in results_list if r['icc'] == icc]
        n_iterations = len(icc_results)

        for alpha in alpha_levels:
            # Count how many p-values are <= alpha (Type I errors under H0)
            # Note: Under H0 (no treatment effect), p-values should be uniformly distributed
            # so the proportion of p <= alpha should be approximately alpha
            errors = sum(1 for r in icc_results if r['p_value'] <= alpha)

            # Compute empirical error rate
            error_rate = errors / n_iterations

            # Compute 95% confidence interval using Clopper-Pearson (Exact) method
            # This is appropriate for binomial proportions
            if errors == 0:
                ci_lower = 0.0
            else:
                ci_lower = stats.beta.ppf(0.025, errors, n_iterations - errors + 1)

            if errors == n_iterations:
                ci_upper = 1.0
            else:
                ci_upper = stats.beta.ppf(0.975, errors + 1, n_iterations - errors)

            results.append({
                'icc': icc,
                'alpha': alpha,
                'error_rate': error_rate,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper
            })

    return pd.DataFrame(results)
