"""
Statistical test wrappers for hypothesis testing.

This module provides standardized interfaces for common statistical tests
used in the data transformation sensitivity analysis pipeline.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Union, List, Tuple, Optional

# Type alias for array-like inputs
ArrayLike = Union[List[float], np.ndarray, pd.Series]


def t_test(
    group1: ArrayLike,
    group2: ArrayLike,
    equal_var: bool = True,
    alternative: str = "two-sided"
) -> Tuple[float, float]:
    """
    Perform an independent two-sample t-test.

    Parameters
    ----------
    group1 : array-like
        First group of data.
    group2 : array-like
        Second group of data.
    equal_var : bool, optional
        If True (default), perform a standard independent 2 sample t-test
        that assumes equal population variances. If False, perform Welch's
        t-test, which does not assume equal population variances.
    alternative : str, optional
        Defines the alternative hypothesis. Default is 'two-sided'.
        Must be one of 'two-sided', 'less', or 'greater'.

    Returns
    -------
    statistic : float
        The t-statistic.
    pvalue : float
        The p-value associated with the hypothesis test.
    """
    # Convert inputs to numpy arrays
    x1 = np.asarray(group1)
    x2 = np.asarray(group2)

    # Remove NaN values if present
    x1 = x1[~np.isnan(x1)]
    x2 = x2[~np.isnan(x2)]

    if len(x1) < 2 or len(x2) < 2:
        raise ValueError("Each group must have at least 2 non-NaN values.")

    result = stats.ttest_ind(
        x1, x2, equal_var=equal_var, alternative=alternative
    )
    return float(result.statistic), float(result.pvalue)


def anova_one_way(
    *groups: ArrayLike
) -> Tuple[float, float]:
    """
    Perform a one-way ANOVA to compare means of two or more independent groups.

    Parameters
    ----------
    *groups : array-like
        Two or more groups of data to compare.

    Returns
    -------
    statistic : float
        The F-statistic.
    pvalue : float
        The p-value associated with the hypothesis test.
    """
    if len(groups) < 2:
        raise ValueError("At least two groups must be provided for ANOVA.")

    # Convert and clean inputs
    clean_groups = []
    for i, g in enumerate(groups):
        arr = np.asarray(g)
        arr = arr[~np.isnan(arr)]
        if len(arr) == 0:
            raise ValueError(f"Group {i+1} contains no valid data after NaN removal.")
        clean_groups.append(arr)

    result = stats.f_oneway(*clean_groups)
    return float(result.statistic), float(result.pvalue)


def shapiro_test(
    data: ArrayLike
) -> Tuple[float, float]:
    """
    Perform the Shapiro-Wilk test for normality.

    Parameters
    ----------
    data : array-like
        The data to test for normality.

    Returns
    -------
    statistic : float
        The W-statistic of the test.
    pvalue : float
        The p-value of the test.

    Notes
    -----
    The null hypothesis is that the data is drawn from a normal distribution.
    A small p-value (typically < 0.05) indicates rejection of the null hypothesis.
    """
    arr = np.asarray(data)
    arr = arr[~np.isnan(arr)]

    if len(arr) < 3:
        raise ValueError("Shapiro-Wilk test requires at least 3 non-NaN values.")
    if len(arr) > 5000:
        # scipy.stats.shapiro has a limit of 5000 for some versions
        # We take a random sample if too large, though typically we filter size earlier
        arr = np.random.choice(arr, size=5000, replace=False)

    result = stats.shapiro(arr)
    return float(result.statistic), float(result.pvalue)


def friedman_test(
    *groups: ArrayLike
) -> Tuple[float, float]:
    """
    Perform the Friedman test for repeated measures.

    This is a non-parametric alternative to repeated measures ANOVA.

    Parameters
    ----------
    *groups : array-like
        Two or more related samples (groups) of data.

    Returns
    -------
    statistic : float
        The chi-squared statistic.
    pvalue : float
        The p-value associated with the hypothesis test.
    """
    if len(groups) < 2:
        raise ValueError("At least two groups must be provided for Friedman test.")

    # Convert and clean inputs
    clean_groups = []
    for i, g in enumerate(groups):
        arr = np.asarray(g)
        arr = arr[~np.isnan(arr)]
        if len(arr) == 0:
            raise ValueError(f"Group {i+1} contains no valid data after NaN removal.")
        clean_groups.append(arr)

    # Ensure all groups have the same length for Friedman test
    lengths = [len(g) for g in clean_groups]
    if len(set(lengths)) != 1:
        # Truncate to the shortest length to maintain alignment
        min_len = min(lengths)
        clean_groups = [g[:min_len] for g in clean_groups]

    result = stats.friedmanchisquare(*clean_groups)
    return float(result.statistic), float(result.pvalue)