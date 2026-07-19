"""
Statistical test implementations.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Optional, Tuple, Union, Callable, Iterator
from scipy import stats
from dataclasses import dataclass, field

@dataclass
class TestResult:
    """Container for test results."""
    p_value: float
    statistic: float

class ScalingMethod:
    """Enum-like class for scaling methods."""
    STANDARDIZATION = "standardization"
    MINMAX = "minmax"
    ROBUST = "robust"

def run_scaled_t_test(group1: np.ndarray, group2: np.ndarray) -> TestResult:
    """
    Run a t-test on two groups.
    
    Args:
        group1: First group data
        group2: Second group data
    
    Returns:
        TestResult with p_value and statistic
    """
    if len(group1) == 0 or len(group2) == 0:
        return TestResult(p_value=1.0, statistic=0.0)
    
    statistic, p_value = stats.ttest_ind(group1, group2)
    return TestResult(p_value=float(p_value), statistic=float(statistic))

def run_scaled_anova(group1: np.ndarray, group2: np.ndarray) -> TestResult:
    """
    Run an ANOVA test on two groups.
    
    Args:
        group1: First group data
        group2: Second group data
    
    Returns:
        TestResult with p_value and statistic
    """
    if len(group1) == 0 or len(group2) == 0:
        return TestResult(p_value=1.0, statistic=0.0)
    
    statistic, p_value = stats.f_oneway(group1, group2)
    return TestResult(p_value=float(p_value), statistic=float(statistic))

def run_scaled_chi_squared(group1: np.ndarray, group2: np.ndarray) -> TestResult:
    """
    Run a Chi-squared test on two groups.
    Note: This requires binning for continuous data.
    
    Args:
        group1: First group data
        group2: Second group data
    
    Returns:
        TestResult with p_value and statistic
    """
    if len(group1) == 0 or len(group2) == 0:
        return TestResult(p_value=1.0, statistic=0.0)
    
    # Bin the data
    all_data = np.concatenate([group1, group2])
    bins = np.linspace(np.min(all_data), np.max(all_data), 11)
    
    hist1, _ = np.histogram(group1, bins=bins)
    hist2, _ = np.histogram(group2, bins=bins)
    
    # Check for zero variance or empty bins
    if np.sum(hist1) == 0 or np.sum(hist2) == 0:
        logging.warning("Edge Case: Zero Variance / Bin Merge Failed")
        return TestResult(p_value=1.0, statistic=0.0)
    
    statistic, p_value = stats.chisquare(f_obs=np.concatenate([hist1, hist2]))
    return TestResult(p_value=float(p_value), statistic=float(statistic))

def run_pipeline(data: Dict[str, np.ndarray], scaling_method: str, test_type: str) -> TestResult:
    """
    Run a full scaling and testing pipeline.
    
    Args:
        data: Dictionary with 'group1' and 'group2' keys
        scaling_method: Method to use for scaling
        test_type: Type of statistical test to run
    
    Returns:
        TestResult
    """
    # Import scaling functions
    from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
    
    scaling_funcs = {
        "standardization": standardize_data,
        "minmax": min_max_scale,
        "robust": robust_scale
    }
    
    test_funcs = {
        "t-test": run_scaled_t_test,
        "anova": run_scaled_anova,
        "chi-squared": run_scaled_chi_squared
    }
    
    scaler = scaling_funcs.get(scaling_method)
    tester = test_funcs.get(test_type)
    
    if not scaler or not tester:
        raise ValueError(f"Unknown scaling method: {scaling_method} or test type: {test_type}")
    
    scaled_group1 = scaler(data['group1'])
    scaled_group2 = scaler(data['group2'])
    
    if scaled_group1 is None or scaled_group2 is None:
        # Handle cases where scaling returned None (e.g., zero IQR)
        return TestResult(p_value=1.0, statistic=0.0)
    
    return tester(scaled_group1, scaled_group2)
