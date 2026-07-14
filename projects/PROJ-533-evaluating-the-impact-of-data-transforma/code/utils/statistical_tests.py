"""
Statistical test wrappers for hypothesis testing.

Provides standardized interfaces for:
- Independent and paired t-tests
- One-way ANOVA
- Shapiro-Wilk normality test
- Friedman non-parametric repeated measures test
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Union, List, Tuple, Optional

ArrayLike = Union[np.ndarray, pd.Series, List[float]]


def t_test(
    group1: ArrayLike,
    group2: ArrayLike,
    paired: bool = False,
    equal_var: bool = True
) -> Tuple[float, float]:
    """
    Perform an independent or paired t-test between two groups.
    
    Args:
        group1: First group of data.
        group2: Second group of data.
        paired: If True, perform a paired t-test. Default is False (independent).
        equal_var: If True, perform standard independent t-test assuming equal variance.
                   If False, perform Welch's t-test. Only used if paired=False.
                   
    Returns:
        Tuple of (statistic, p-value).
        
    Raises:
        ValueError: If input arrays are empty or have incompatible shapes for paired test.
    """
    arr1 = np.asarray(group1)
    arr2 = np.asarray(group2)
    
    if arr1.size == 0 or arr2.size == 0:
        raise ValueError("Input arrays cannot be empty.")
        
    if paired:
        if arr1.shape != arr2.shape:
            raise ValueError("For paired t-test, both groups must have the same shape.")
        stat, p_val = stats.ttest_rel(arr1, arr2)
    else:
        stat, p_val = stats.ttest_ind(arr1, arr2, equal_var=equal_var)
        
    return float(stat), float(p_val)


def anova_one_way(groups: List[ArrayLike]) -> Tuple[float, float]:
    """
    Perform a one-way ANOVA to test if there are statistically significant 
    differences between the means of three or more independent groups.
    
    Args:
        groups: List of arrays, where each array represents a group's data.
                
    Returns:
        Tuple of (F-statistic, p-value).
        
    Raises:
        ValueError: If fewer than 2 groups are provided or if any group is empty.
    """
    if len(groups) < 2:
        raise ValueError("At least two groups are required for ANOVA.")
        
    np_groups = [np.asarray(g) for g in groups]
    
    if any(g.size == 0 for g in np_groups):
        raise ValueError("All groups must contain data.")
        
    stat, p_val = stats.f_oneway(*np_groups)
    
    return float(stat), float(p_val)


def shapiro_test(data: ArrayLike) -> Tuple[float, float]:
    """
    Perform the Shapiro-Wilk test for normality.
    
    The null hypothesis is that the data is normally distributed.
    A small p-value (< 0.05) suggests the data is NOT normally distributed.
    
    Args:
        data: Array of data values.
        
    Returns:
        Tuple of (statistic, p-value).
        
    Raises:
        ValueError: If data has fewer than 3 observations or more than 5000 
                    (scipy limit for older versions, though newer handles more).
    """
    arr = np.asarray(data)
    
    if arr.size < 3:
        raise ValueError("Shapiro-Wilk test requires at least 3 observations.")
        
    if arr.size > 5000:
        # For very large samples, Shapiro-Wilk can be computationally expensive
        # We proceed but scipy might have limits depending on version.
        pass
        
    stat, p_val = stats.shapiro(arr)
    
    return float(stat), float(p_val)


def friedman_test(groups: List[ArrayLike]) -> Tuple[float, float]:
    """
    Perform the Friedman test for comparing related samples (repeated measures).
    
    This is a non-parametric alternative to repeated measures ANOVA.
    The null hypothesis is that the related samples come from the same distribution.
    
    Args:
        groups: List of arrays, where each array represents a condition/group.
                All groups must have the same number of observations (subjects).
                
    Returns:
        Tuple of (Chi-squared statistic, p-value).
        
    Raises:
        ValueError: If fewer than 2 groups are provided or if groups have 
                    inconsistent lengths.
    """
    if len(groups) < 2:
        raise ValueError("At least two groups are required for Friedman test.")
        
    np_groups = [np.asarray(g) for g in groups]
    
    # Check for consistent lengths (subjects)
    first_len = len(np_groups[0])
    for i, g in enumerate(np_groups[1:], 1):
        if len(g) != first_len:
            raise ValueError(
                f"All groups must have the same number of observations. "
                f"Group 0 has {first_len}, Group {i} has {len(g)}."
            )
            
    stat, p_val = stats.friedmanchisquare(*np_groups)
    
    return float(stat), float(p_val)