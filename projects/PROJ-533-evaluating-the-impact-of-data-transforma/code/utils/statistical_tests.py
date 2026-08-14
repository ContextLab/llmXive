import numpy as np
import pandas as pd
from scipy import stats
from typing import Union, List, Tuple, Optional

def t_test(group1: list, group2: list) -> float:
    """Performs an independent samples t-test."""
    t_statistic, p_value = stats.ttest_ind(group1, group2)
    return p_value

def anova_one_way(groups: List[list]) -> float:
    """Performs a one-way ANOVA test."""
    f_statistic, p_value = stats.f_oneway(*groups)
    return p_value

def shapiro_test(data: list) -> float:
    """Performs the Shapiro-Wilk normality test."""
    w_statistic, p_value = stats.shapiro(data)
    return p_value

def friedman_test(groups: List[list]) -> float:
    """Performs the Friedman test for non-parametric repeated measures ANOVA."""
    statistic, p_value = stats.friedmanchisquare(*groups)
    return p_value
