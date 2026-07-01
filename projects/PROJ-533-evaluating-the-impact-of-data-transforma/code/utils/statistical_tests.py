"""
Statistical test wrappers for the llmXive pipeline.

Provides consistent interfaces for t-tests, ANOVA, Shapiro-Wilk, and Friedman tests.
Handles input validation and returns standardized result dictionaries.
"""

from typing import List, Tuple, Union, Dict, Any, Optional
import numpy as np
from scipy import stats

# Type alias for array-like input
ArrayLike = Union[List[float], np.ndarray]


def independent_t_test(
    group1: ArrayLike,
    group2: ArrayLike,
    equal_variance: bool = False
) -> Dict[str, Any]:
    """
    Perform an independent two-sample t-test.

    Args:
        group1: Data for the first group.
        group2: Data for the second group.
        equal_variance: If True, use Student's t-test (equal variance).
                        If False, use Welch's t-test (unequal variance).

    Returns:
        Dictionary containing:
            - 'statistic': float, t-statistic
            - 'p_value': float, two-tailed p-value
            - 'test_type': str, 'welch' or 'student'
    """
    arr1 = np.asarray(group1, dtype=float)
    arr2 = np.asarray(group2, dtype=float)

    if arr1.size == 0 or arr2.size == 0:
        raise ValueError("Input arrays cannot be empty.")

    result = stats.ttest_ind(arr1, arr2, equal_var=equal_variance)

    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "test_type": "welch" if not equal_variance else "student"
    }


def one_way_anova(*groups: ArrayLike) -> Dict[str, Any]:
    """
    Perform a one-way ANOVA.

    Args:
        *groups: Variable number of array-like groups.

    Returns:
        Dictionary containing:
            - 'statistic': float, F-statistic
            - 'p_value': float, p-value
    """
    if len(groups) < 2:
        raise ValueError("At least two groups are required for ANOVA.")

    arrays = [np.asarray(g, dtype=float) for g in groups]

    if any(arr.size == 0 for arr in arrays):
        raise ValueError("Input groups cannot be empty.")

    result = stats.f_oneway(*arrays)

    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue)
    }


def shapiro_wilk(data: ArrayLike) -> Dict[str, Any]:
    """
    Perform the Shapiro-Wilk test for normality.

    Args:
        data: Array-like data to test.

    Returns:
        Dictionary containing:
            - 'statistic': float, W statistic
            - 'p_value': float, p-value
    """
    arr = np.asarray(data, dtype=float)

    if arr.size < 3:
        raise ValueError("Shapiro-Wilk test requires at least 3 data points.")

    result = stats.shapiro(arr)

    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue)
    }


def friedman_test(*groups: ArrayLike) -> Dict[str, Any]:
    """
    Perform the Friedman test for repeated measures.

    Args:
        *groups: Variable number of array-like groups (conditions).
                 All groups must have the same length (subjects).

    Returns:
        Dictionary containing:
            - 'statistic': float, Chi-squared statistic
            - 'p_value': float, p-value
    """
    if len(groups) < 2:
        raise ValueError("At least two groups are required for Friedman test.")

    arrays = [np.asarray(g, dtype=float) for g in groups]
    n_groups = len(arrays)

    # Validate that all groups have the same length
    lengths = [len(arr) for arr in arrays]
    if len(set(lengths)) != 1:
        raise ValueError(
            f"All groups must have the same number of observations. "
            f"Found lengths: {lengths}"
        )

    if arrays[0].size == 0:
        raise ValueError("Input groups cannot be empty.")

    # Convert to 2D array (rows=subjects, cols=conditions)
    data_matrix = np.column_stack(arrays)

    result = stats.friedmanchisquare(*arrays)

    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue)
    }


def get_test_summary(test_name: str) -> str:
    """
    Return a description of a supported statistical test.

    Args:
        test_name: Name of the test (e.g., 't-test', 'anova', 'shapiro', 'friedman').

    Returns:
        String description of the test.
    """
    descriptions = {
        "t-test": "Independent two-sample t-test (Student or Welch).",
        "anova": "One-way Analysis of Variance.",
        "shapiro": "Shapiro-Wilk test for normality.",
        "friedman": "Friedman test for repeated measures (non-parametric ANOVA)."
    }
    return descriptions.get(test_name.lower(), "Unknown test.")
