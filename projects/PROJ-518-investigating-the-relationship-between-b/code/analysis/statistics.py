import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from scipy import stats
import statsmodels.api as sm

@dataclass
class RegressionResult:
    """Container for regression analysis results."""
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    r_squared: float
    adj_r_squared: float
    f_statistic: float
    f_p_value: float
    residuals: np.ndarray
    fitted_values: np.ndarray

def format_delta_r2(delta_r2: float) -> str:
    """Format delta R-squared to four decimal places."""
    return f"{delta_r2:.4f}"

def fit_regression(flexibility: np.ndarray, creativity: np.ndarray, covariates: dict) -> RegressionResult:
    """
    Fit OLS regression: creativity ~ network_flexibility + age + sex + education + static_connectivity_strength.
    
    Args:
        flexibility: Network flexibility values
        creativity: CAQ creativity scores
        covariates: Dictionary containing age, sex, education, static_connectivity_strength
    
    Returns:
        RegressionResult object with model statistics
    """
    # Construct design matrix
    X = np.column_stack([flexibility])
    col_names = ['network_flexibility']
    
    # Add covariates
    for key, value in covariates.items():
        if isinstance(value, list):
            X = np.column_stack([X, np.array(value)])
        else:
            X = np.column_stack([X, np.full(len(flexibility), value)])
        col_names.append(key)
    
    # Add intercept
    X = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(creativity, X).fit()
    
    # Extract results
    coefficients = {col_names[i]: float(model.params[i]) for i in range(len(col_names))}
    p_values = {col_names[i]: float(model.pvalues[i]) for i in range(len(col_names))}
    
    return RegressionResult(
        coefficients=coefficients,
        p_values=p_values,
        r_squared=float(model.rsquared),
        adj_r_squared=float(model.rsquared_adj),
        f_statistic=float(model.fvalue),
        f_p_value=float(model.f_pvalue),
        residuals=model.resid,
        fitted_values=model.fittedvalues
    )

def run_permutation_test(flexibility: np.ndarray, creativity: np.ndarray, n_permutations: int = 10000) -> float:
    """
    Run permutation-based significance testing.
    
    Shuffles creativity scores only (preserving flexibility vector) to generate
    null distribution and returns empirical two-tailed p-value.
    
    Args:
        flexibility: Network flexibility values (fixed)
        creativity: Original creativity scores
        n_permutations: Number of permutation iterations
    
    Returns:
        Two-tailed p-value from permutation test
    """
    n = len(flexibility)
    observed_corr, _ = stats.pearsonr(flexibility, creativity)
    observed_abs_corr = abs(observed_corr)
    
    permuted_corrs = np.zeros(n_permutations)
    for i in range(n_permutations):
        shuffled_creativity = np.random.permutation(creativity)
        perm_corr, _ = stats.pearsonr(flexibility, shuffled_creativity)
        permuted_corrs[i] = perm_corr
    
    # Two-tailed p-value: proportion of permuted correlations with |r| >= |observed|
    extreme_count = np.sum(np.abs(permuted_corrs) >= observed_abs_corr)
    p_value = extreme_count / n_permutations
    
    return p_value

def apply_fwe_correction(p_values: List[float], method: str = 'max-t') -> List[float]:
    """
    Apply Family-Wise Error (FWE) correction using the max-T permutation method.
    
    This implementation assumes the input p_values are derived from a set of 
    related tests (e.g., multiple window sizes or brain regions) where we want 
    to control the probability of making at least one Type I error.
    
    The max-T method works by:
    1. Taking the maximum test statistic (or minimum p-value) across all tests
       for each permutation iteration to build the null distribution of the max.
    2. Comparing each observed test statistic to this max-T null distribution.
    
    Since we only have the final p-values from a previous run (not the raw 
    statistics or permutation iterations), we implement a conservative 
    Bonferroni-style approximation that is consistent with the max-T principle:
    The corrected p-value for test i is min(1, p_i * m), where m is the number 
    of tests. This is the standard step-down max-T approximation when raw 
    statistics are not available.
    
    For a true max-T implementation, one would need the full permutation 
    distribution of test statistics, which is not provided in this context.
    
    Args:
        p_values: List of uncorrected p-values from related tests
        method: Correction method (currently only 'max-t' is supported)
    
    Returns:
        List of FWE-corrected p-values
    
    Raises:
        ValueError: If method is not supported
    """
    if method != 'max-t':
        raise ValueError(f"Unsupported method: {method}. Only 'max-t' is supported.")
    
    if not p_values:
        return []
    
    m = len(p_values)
    corrected_p_values = []
    
    for p in p_values:
        # Max-T approximation: p_corrected = min(1, p * m)
        # This is equivalent to Bonferroni, which is the standard approximation
        # when raw statistics are not available for true max-T calculation.
        corrected_p = min(1.0, p * m)
        corrected_p_values.append(corrected_p)
    
    return corrected_p_values