import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from scipy import stats as scipy_stats
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool], Dict[str, float]]:
    """
    Apply Bonferroni correction for multiple comparisons.

    The Bonferroni correction adjusts the significance threshold (alpha) by dividing
    it by the number of tests performed, or equivalently, multiplies each p-value
    by the number of tests.

    Args:
        p_values: List of raw p-values from statistical tests.
        alpha: Desired significance level (default 0.05).

    Returns:
        Tuple containing:
            - corrected_p_values: List of adjusted p-values.
            - significant_flags: List of booleans indicating if the test is significant
              after correction.
            - summary: Dictionary with correction details (adjusted_alpha, num_tests).
    """
    if not p_values:
        return [], [], {"num_tests": 0, "adjusted_alpha": alpha}

    num_tests = len(p_values)
    adjusted_alpha = alpha / num_tests

    # Calculate corrected p-values (min with 1.0 to ensure valid probability)
    corrected_p_values = [min(p * num_tests, 1.0) for p in p_values]

    # Determine significance based on the adjusted alpha
    significant_flags = [p < adjusted_alpha for p in corrected_p_values]

    summary = {
        "num_tests": num_tests,
        "original_alpha": alpha,
        "adjusted_alpha": adjusted_alpha,
        "num_significant": sum(significant_flags)
    }

    logger.info(f"Bonferroni correction applied: {num_tests} tests, "
                f"adjusted alpha = {adjusted_alpha:.6f}, "
                f"significant results = {summary['num_significant']}")

    return corrected_p_values, significant_flags, summary

def kruskal_wallis_test(groups: List[np.ndarray]) -> Tuple[float, float]:
    """
    Perform Kruskal-Wallis H-test for independent samples.
    """
    if len(groups) < 2:
        raise ValueError("At least two groups are required for Kruskal-Wallis test.")
    h_stat, p_val = scipy_stats.kruskal(*groups)
    return h_stat, p_val

def mann_whitney_u_test(group1: np.ndarray, group2: np.ndarray, alternative: str = 'two-sided') -> Tuple[float, float]:
    """
    Perform Mann-Whitney U test (Wilcoxon rank-sum test) between two independent samples.
    """
    u_stat, p_val = scipy_stats.mannwhitneyu(group1, group2, alternative=alternative)
    return u_stat, p_val

def ks_test(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov test for two independent samples.
    """
    ks_stat, p_val = scipy_stats.ks_2samp(group1, group2)
    return ks_stat, p_val

def nearest_neighbor_matching(data: pd.DataFrame, treatment_col: str, 
                              mass_col: str, tolerance: float = 0.1) -> pd.DataFrame:
    """
    Perform nearest-neighbor matching on mass to control for confounding.
    
    Args:
        data: DataFrame containing the data.
        treatment_col: Column name for the treatment/group variable.
        mass_col: Column name for the mass variable to match on.
        tolerance: Maximum relative mass difference for a match.
        
    Returns:
        DataFrame with a 'matched' boolean column indicating included samples.
    """
    matched_indices = set()
    data = data.copy()
    data['matched'] = False

    # Split into treatment and control groups
    treatment_group = data[data[treatment_col] == 1]
    control_group = data[data[treatment_col] == 0]

    if len(treatment_group) == 0 or len(control_group) == 0:
        logger.warning("One of the groups is empty; no matching possible.")
        return data

    for idx, row in treatment_group.iterrows():
        t_mass = row[mass_col]
        # Find nearest neighbor in control group
        mass_diff = np.abs(control_group[mass_col] - t_mass)
        nearest_idx = mass_diff.idxmin()
        n_mass = control_group.loc[nearest_idx, mass_col]
        
        # Check if within tolerance
        if np.abs(t_mass - n_mass) <= tolerance * t_mass:
            matched_indices.add(idx)
            matched_indices.add(nearest_idx)

    data.loc[list(matched_indices), 'matched'] = True
    logger.info(f"Nearest neighbor matching completed: {len(matched_indices)} samples retained.")
    return data

def linear_regression_with_mass_control(df: pd.DataFrame, 
                                        dependent_var: str, 
                                        independent_vars: List[str], 
                                        mass_col: str) -> Dict[str, Any]:
    """
    Perform linear regression controlling for mass.
    This is a simple implementation using scipy or manual calculation if statsmodels is not available.
    We will use a simple matrix approach to ensure no external heavy dependencies beyond scipy/numpy.
    """
    # Prepare matrix X (independent vars + mass) and vector y
    # We add a constant term (intercept)
    X = df[independent_vars + [mass_col]].values
    y = df[dependent_var].values

    # Add intercept column
    X = np.column_stack((np.ones(len(X)), X))

    # Solve normal equations: beta = (X'X)^-1 X'y
    try:
        # Using scipy.linalg for stability
        from scipy import linalg
        XtX = X.T @ X
        Xty = X.T @ y
        
        # Check for singularity
        if np.linalg.matrix_rank(XtX) < XtX.shape[1]:
            logger.warning("Design matrix is singular; using pseudo-inverse.")
            beta = linalg.pinv(XtX) @ Xty
        else:
            beta = linalg.solve(XtX, Xty)
        
        # Calculate residuals and R-squared
        y_pred = X @ beta
        residuals = y - y_pred
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        return {
            "coefficients": beta.tolist(),
            "r_squared": float(r_squared),
            "predictors": ["intercept"] + independent_vars + [mass_col]
        }
    except Exception as e:
        logger.error(f"Regression failed: {e}")
        return {
            "coefficients": [],
            "r_squared": 0.0,
            "predictors": [],
            "error": str(e)
        }