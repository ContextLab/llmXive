import numpy as np
import pandas as pd
from scipy import stats
from typing import Union, List, Tuple, Optional


def t_test(
    group1: Union[np.ndarray, List[float], pd.Series],
    group2: Union[np.ndarray, List[float], pd.Series],
    equal_var: bool = True
) -> Tuple[float, float]:
    """
    Perform an independent two-sample t-test.

    Args:
        group1: Data for the first group.
        group2: Data for the second group.
        equal_var: If True (default), perform standard Student's t-test assuming equal
                   population variances. If False, perform Welch's t-test.

    Returns:
        A tuple (statistic, p_value).

    Raises:
        ValueError: If input arrays are empty or contain non-numeric data.
    """
    arr1 = np.asarray(group1)
    arr2 = np.asarray(group2)

    if arr1.size == 0 or arr2.size == 0:
        raise ValueError("Input arrays cannot be empty.")

    if not np.issubdtype(arr1.dtype, np.number) or not np.issubdtype(arr2.dtype, np.number):
        raise ValueError("Input arrays must contain numeric data.")

    statistic, p_value = stats.ttest_ind(arr1, arr2, equal_var=equal_var)
    return float(statistic), float(p_value)


def anova_one_way(
    groups: Union[List[Union[np.ndarray, List[float], pd.Series]], np.ndarray]
) -> Tuple[float, float]:
    """
    Perform a one-way ANOVA test.

    Args:
        groups: A list of array-like data groups, or a 2D array where each row/column
                represents a group.

    Returns:
        A tuple (f_statistic, p_value).

    Raises:
        ValueError: If fewer than 2 groups are provided or if data is invalid.
    """
    if isinstance(groups, np.ndarray) and groups.ndim == 2:
        # If 2D, treat rows as groups if shape[0] < shape[1], else columns
        # Standard scipy expects *args, so we unpack.
        # If passed as a list of arrays, we unpack that too.
        pass

    if isinstance(groups, list):
        if len(groups) < 2:
            raise ValueError("ANOVA requires at least 2 groups.")
        arrays = [np.asarray(g) for g in groups]
    elif isinstance(groups, np.ndarray) and groups.ndim == 2:
        # Assuming rows are groups for 2D input in this context, or columns.
        # Let's assume the user passes a list of arrays for clarity,
        # but handle 2D array by iterating rows.
        if groups.shape[0] < 2:
            raise ValueError("ANOVA requires at least 2 groups.")
        arrays = [groups[i, :] for i in range(groups.shape[0])]
    else:
        raise ValueError("Input must be a list of groups or a 2D numpy array.")

    # Validate data
    for i, arr in enumerate(arrays):
        if arr.size == 0:
            raise ValueError(f"Group {i} is empty.")
        if not np.issubdtype(arr.dtype, np.number):
            raise ValueError(f"Group {i} contains non-numeric data.")

    statistic, p_value = stats.f_oneway(*arrays)
    return float(statistic), float(p_value)


def shapiro_test(
    data: Union[np.ndarray, List[float], pd.Series]
) -> Tuple[float, float]:
    """
    Perform the Shapiro-Wilk test for normality.

    Args:
        data: Array-like data to test.

    Returns:
        A tuple (statistic, p_value).

    Raises:
        ValueError: If data is too small (n < 3) or too large (n > 5000) for this test,
                    or if data is not numeric.
    """
    arr = np.asarray(data)

    if arr.size < 3:
        raise ValueError("Shapiro-Wilk test requires at least 3 samples.")
    if arr.size > 5000:
        raise ValueError("Shapiro-Wilk test is limited to 5000 samples. "
                         "Consider using the Anderson-Darling test for larger datasets.")
    if not np.issubdtype(arr.dtype, np.number):
        raise ValueError("Input data must be numeric.")

    statistic, p_value = stats.shapiro(arr)
    return float(statistic), float(p_value)


def friedman_test(
    data: Union[np.ndarray, pd.DataFrame]
) -> Tuple[float, float]:
    """
    Perform the Friedman test (non-parametric repeated measures ANOVA).

    Args:
        data: A 2D array or DataFrame where rows are blocks (subjects) and columns
              are treatments (groups).

    Returns:
        A tuple (chi2_statistic, p_value).

    Raises:
        ValueError: If data is not 2D or does not have at least 2 groups (columns).
    """
    if isinstance(data, pd.DataFrame):
        arr = data.values
    else:
        arr = np.asarray(data)

    if arr.ndim != 2:
        raise ValueError("Input data must be 2D (rows=blocks, columns=treatments).")
    if arr.shape[1] < 2:
        raise ValueError("Friedman test requires at least 2 groups (columns).")
    if arr.shape[0] < 2:
        raise ValueError("Friedman test requires at least 2 blocks (rows).")

    if not np.issubdtype(arr.dtype, np.number):
        raise ValueError("Input data must be numeric.")

    # Handle NaNs if any (scipy might raise, so we check or let it fail loudly)
    if np.isnan(arr).any():
        raise ValueError("Input data contains NaN values. Please handle missing data before testing.")

    statistic, p_value = stats.friedmanchisquare(*arr.T)
    return float(statistic), float(p_value)
