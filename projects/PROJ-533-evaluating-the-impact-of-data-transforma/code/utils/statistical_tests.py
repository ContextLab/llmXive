"""
Statistical test wrappers for the data transformation sensitivity pipeline.

This module provides standardized interfaces for common statistical tests:
- t_test: Independent samples t-test
- anova: One-way ANOVA
- shapiro_wilk: Shapiro-Wilk normality test
- glmm: Generalized Linear Mixed Model

All functions accept numpy arrays or pandas DataFrames and return results
suitable for aggregation and reporting.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Union, List, Tuple, Optional, Dict, Any
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.regression.mixed_linear_model import MixedLM


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


def anova(groups: Union[List[np.ndarray], np.ndarray]) -> float:
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

    # Filter out any empty groups if they exist
    valid_groups = [g for g in group_list if len(g) > 0]

    if len(valid_groups) < 2:
        raise ValueError("Need at least two non-empty groups for ANOVA.")

    statistic, p_value = stats.f_oneway(*valid_groups)
    return float(p_value)


def shapiro_wilk(data: np.ndarray) -> Tuple[float, float]:
    """
    Perform the Shapiro-Wilk test for normality.

    Args:
        data: The data sample (numpy array).

    Returns:
        Tuple[float, float]: A tuple containing (statistic, p_value).
    """
    if len(data) < 3:
        raise ValueError("Shapiro-Wilk test requires at least 3 samples.")
    
    # scipy.stats.shapiro has a limit of 5000 samples in older versions.
    # If data is larger, we sample 5000 points for the test to ensure compatibility
    # while maintaining the statistical validity of the normality check.
    if len(data) > 5000:
        data = np.random.choice(data, size=5000, replace=False)

    statistic, p_value = stats.shapiro(data)
    return float(statistic), float(p_value)


def glmm(data: pd.DataFrame, 
         dependent_var: str, 
         independent_var: str, 
         grouping_var: str) -> Dict[str, Any]:
    """
    Perform a Generalized Linear Mixed Model (GLMM) analysis.
    
    This function fits a linear mixed-effects model where the dependent variable
    is modeled as a function of the independent variable with random intercepts
    for the grouping variable.

    Args:
        data: DataFrame containing the data.
        dependent_var: Name of the dependent variable column.
        independent_var: Name of the independent variable column.
        grouping_var: Name of the grouping variable column (random effect).

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'p_value': p-value for the independent variable
            - 'coefficient': coefficient estimate for the independent variable
            - 'std_err': standard error of the coefficient
            - 'model_summary': string representation of the model summary
    """
    if dependent_var not in data.columns or independent_var not in data.columns or grouping_var not in data.columns:
        raise ValueError("Specified columns not found in data.")

    # Ensure grouping variable is categorical
    data = data.copy()
    data[grouping_var] = data[grouping_var].astype('category')

    # Formula for mixed model: dependent ~ independent + (1|grouping)
    formula = f"{dependent_var} ~ {independent_var}"
    
    try:
        # Fit the mixed linear model
        model = smf.mixedlm(formula, data, groups=data[grouping_var])
        result = model.fit()
        
        # Extract p-value for the independent variable
        # The summary table contains p-values
        p_value = result.pvalues[independent_var]
        coefficient = result.params[independent_var]
        std_err = result.bse[independent_var]
        
        return {
            'p_value': float(p_value),
            'coefficient': float(coefficient),
            'std_err': float(std_err),
            'model_summary': str(result.summary())
        }
    except Exception as e:
        # If fitting fails (e.g., convergence issues), return error info
        return {
            'p_value': None,
            'coefficient': None,
            'std_err': None,
            'model_summary': f"Model fitting failed: {str(e)}",
            'error': str(e)
        }