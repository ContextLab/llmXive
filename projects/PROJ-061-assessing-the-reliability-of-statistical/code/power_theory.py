"""
Theoretical power calculation for two-sample t-test.
"""
import logging
from typing import Optional

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

def theoretical_power_ttest(
    n1: int,
    n2: int,
    d: float,
    alpha: float = 0.05,
    alternative: str = "two-sided"
) -> float:
    """
    Calculate the theoretical statistical power for a two-sample t-test.

    Parameters:
    -----------
    n1 : int
        Sample size of group 1.
    n2 : int
        Sample size of group 2.
    d : float
        Effect size (Cohen's d).
    alpha : float
        Significance level.
    alternative : str
        Type of test: "two-sided", "greater", or "less".

    Returns:
    --------
    float
        The calculated power (probability of rejecting the null hypothesis).
    """
    # Calculate degrees of freedom
    df = n1 + n2 - 2

    # Calculate non-centrality parameter (ncp)
    # ncp = d * sqrt((n1 * n2) / (n1 + n2))
    ncp = d * np.sqrt((n1 * n2) / (n1 + n2))

    # Determine critical t-value
    if alternative == "two-sided":
        t_crit = stats.t.ppf(1 - alpha / 2, df)
    elif alternative == "greater":
        t_crit = stats.t.ppf(1 - alpha, df)
    elif alternative == "less":
        t_crit = stats.t.ppf(alpha, df)
    else:
        raise ValueError(f"Invalid alternative hypothesis: {alternative}")

    # Calculate power
    # Power = P(T > t_crit | H1) for one-sided greater
    # For two-sided, it's more complex, but scipy's nct.cdf can handle it.
    # We use the non-central t-distribution.
    if alternative == "two-sided":
        # Probability of rejecting in either tail
        # P(T > t_crit) + P(T < -t_crit)
        power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    elif alternative == "greater":
        power = 1 - stats.nct.cdf(t_crit, df, ncp)
    elif alternative == "less":
        power = stats.nct.cdf(t_crit, df, ncp)

    return float(power)
