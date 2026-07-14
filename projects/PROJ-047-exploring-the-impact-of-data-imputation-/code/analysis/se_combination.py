"""
Standard Error and Confidence Interval Combination Logic.

Provides functions to calculate robust standard errors and confidence intervals
for causal estimates using:
1. Rubin's Rules (for MICE imputation results)
2. Bootstrap CI (for Mean/KNN imputation results by resampling estimates)
"""

import numpy as np
from typing import List, Tuple, Optional
from scipy import stats

from .entities import CausalEstimate


def apply_rubins_rules(estimates_list: List[CausalEstimate]) -> CausalEstimate:
    """
    Apply Rubin's Rules to combine multiple causal estimates (typically from MICE).

    Rubin's Rules calculate the pooled estimate and total variance accounting for
    both within-imputation and between-imputation variance.

    Parameters
    ----------
    estimates_list : List[CausalEstimate]
        List of CausalEstimate objects, each representing an estimate from a
        different imputed dataset. Must all have valid 'ate' and 'se' values.

    Returns
    -------
    CausalEstimate
        A new CausalEstimate with:
        - ate: The pooled mean of the estimates
        - se: The square root of the total variance (Rubin's combination)
        - ci_lower, ci_upper: 95% confidence intervals based on pooled SE
        - method: "rubins_combined"
    """
    if not estimates_list:
        raise ValueError("estimates_list cannot be empty")

    if len(estimates_list) == 1:
        # If only one estimate, return it as is
        return estimates_list[0]

    # Extract ATEs and standard errors
    ates = np.array([est.ate for est in estimates_list])
    ses = np.array([est.se for est in estimates_list])

    # Validate inputs
    if np.any(np.isnan(ates)) or np.any(np.isnan(ses)):
        raise ValueError("Estimates contain NaN values")

    m = len(estimates_list)  # Number of imputations

    # 1. Pooled estimate (Q_bar)
    q_bar = np.mean(ates)

    # 2. Within-imputation variance (U_bar)
    # Variance of the estimate within each imputation
    u_bar = np.mean(ses ** 2)

    # 3. Between-imputation variance (B)
    # Variance of the estimates across imputations
    b = np.var(ates, ddof=1)

    # 4. Total variance (T)
    # T = U_bar + (1 + 1/m) * B
    t = u_bar + (1 + 1/m) * b

    # 5. Pooled standard error
    se_pooled = np.sqrt(t)

    # 6. Degrees of freedom for Rubin's rules
    # Lambda = B / T (fraction of missing information)
    lambda_frac = b / t if t > 0 else 0

    # Gamma_0 = (1 + 1/m) * B / T
    gamma_0 = (1 + 1/m) * lambda_frac

    # Degrees of freedom (df)
    # df = (m - 1) * (1 + 1/(m * gamma_0))^2
    # But if gamma_0 is 0, df is infinite (use normal approx)
    if gamma_0 == 0 or np.isnan(gamma_0):
        df = np.inf
    else:
        df = (m - 1) * (1 + 1 / (m * gamma_0)) ** 2

    # 7. Confidence Intervals (95%)
    # Use t-distribution if finite df, else normal
    if np.isinf(df):
        crit_val = stats.norm.ppf(0.975)
    else:
        crit_val = stats.t.ppf(0.975, df)

    ci_lower = q_bar - crit_val * se_pooled
    ci_upper = q_bar + crit_val * se_pooled

    return CausalEstimate(
        ate=q_bar,
        se=se_pooled,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        method="rubins_combined",
        estimator="mice_combined"
    )


def apply_bootstrap_ci(ate_estimates: List[float], n_boot: int = 1000) -> Tuple[float, float, float]:
    """
    Calculate robust standard error and confidence intervals via bootstrapping
    the ATE estimates.

    This function resamples the provided ATE estimates (not the raw data) with
    replacement to estimate the sampling distribution of the ATE.

    Parameters
    ----------
    ate_estimates : List[float]
        List of ATE estimates (e.g., from multiple runs or bootstrap samples).
    n_boot : int
        Number of bootstrap resamples to generate.

    Returns
    -------
    Tuple[float, float, float]
        (mean_ate, se_boot, ci_95_lower, ci_95_upper)
        - mean_ate: Mean of the input estimates
        - se_boot: Standard deviation of the bootstrap distribution
        - ci_95_lower: Lower bound of 95% CI (percentile method)
        - ci_95_upper: Upper bound of 95% CI (percentile method)
    """
    if not ate_estimates:
        raise ValueError("ate_estimates cannot be empty")

    estimates_arr = np.array(ate_estimates)

    if np.any(np.isnan(estimates_arr)):
        raise ValueError("ate_estimates contains NaN values")

    n = len(estimates_arr)
    rng = np.random.default_rng()

    # Bootstrap resampling of the estimates
    bootstrap_means = []
    for _ in range(n_boot):
        # Resample with replacement
        resample = rng.choice(estimates_arr, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))

    bootstrap_means = np.array(bootstrap_means)

    # Calculate statistics
    mean_ate = np.mean(bootstrap_means)
    se_boot = np.std(bootstrap_means, ddof=1)

    # Percentile confidence interval (95%)
    ci_lower = np.percentile(bootstrap_means, 2.5)
    ci_upper = np.percentile(bootstrap_means, 97.5)

    return mean_ate, se_boot, ci_lower, ci_upper