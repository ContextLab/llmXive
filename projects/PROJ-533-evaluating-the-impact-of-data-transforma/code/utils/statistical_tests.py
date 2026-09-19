"""
Statistical test wrappers for the data transformation sensitivity pipeline.

This module provides standardized interfaces for common statistical tests:
- t_test: Independent samples t-test
- anova_one_way: One-way ANOVA
- shapiro_test: Shapiro-Wilk normality test
- friedman_test: Friedman test for repeated measures

All functions accept numpy arrays and return p-values (and statistics where applicable).
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Union, List, Tuple, Optional


def t_test(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Perform an independent two-sample t-test.

    Args:
        group1: First group of data (numpy array).
        group2: Second group of data (numpy array).

    Returns:
        float: The p-value of the test.
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Both groups must have at least 2 samples for t-test.")

    statistic, p_value = stats.ttest_ind(group1, group2)
    return float(p_value)


def anova_one_way(groups: Union[List[np.ndarray], np.ndarray]) -> float:
    """
    Perform a one-way ANOVA.

    Args:
        groups: A list of numpy arrays, where each array represents a group,
                or a single 2D numpy array where rows are groups.

    Returns:
        float: The p-value of the ANOVA test.
    """
    if isinstance(groups, np.ndarray):
        if groups.ndim == 1:
            raise ValueError("Input must be a list of groups or a 2D array.")
        # Convert 2D array to list of rows
        group_list = [groups[i] for i in range(groups.shape[0])]
    else:
        group_list = groups

    if len(group_list) < 2:
        raise ValueError("At least two groups are required for ANOVA.")

    # Filter out any empty groups if they exist (though unlikely in valid input)
    valid_groups = [g for g in group_list if len(g) > 0]

    if len(valid_groups) < 2:
        raise ValueError("Need at least two non-empty groups for ANOVA.")

    statistic, p_value = stats.f_oneway(*valid_groups)
    return float(p_value)


def shapiro_test(data: np.ndarray) -> Tuple[float, float]:
    """
    Perform the Shapiro-Wilk test for normality.

    Args:
        data: The data sample (numpy array).

    Returns:
        Tuple[float, float]: A tuple containing (statistic, p_value).
    """
    if len(data) < 3 or len(data) > 5000:
        # scipy.stats.shapiro has limits, though 5000 is the hard limit in older versions.
        # We'll let scipy handle the specific error if out of bounds, but warn if too small.
        if len(data) < 3:
            raise ValueError("Shapiro-Wilk test requires at least 3 samples.")

    statistic, p_value = stats.shapiro(data)
    return float(statistic), float(p_value)


def friedman_test(data_matrix: np.ndarray) -> Tuple[float, float]:
    """
    Perform the Friedman test (non-parametric repeated measures ANOVA).

    Args:
        data_matrix: A 2D numpy array where rows represent subjects and columns represent conditions.

    Returns:
        Tuple[float, float]: A tuple containing (statistic, p_value).
    """
    if data_matrix.ndim != 2:
        raise ValueError("Input must be a 2D array (subjects x conditions).")

    if data_matrix.shape[0] < 2 or data_matrix.shape[1] < 2:
        raise ValueError("Need at least 2 subjects and 2 conditions for Friedman test.")

    statistic, p_value = stats.friedmanchisquare(*data_matrix.T)
    return float(statistic), float(p_value)