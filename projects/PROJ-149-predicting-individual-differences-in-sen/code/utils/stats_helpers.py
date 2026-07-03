"""
Statistical helpers for the EEG analysis pipeline.
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional
import warnings

def bonferroni_correct(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Parameters
    ----------
    p_values : List[float]
        List of p-values to correct.
    alpha : float
        Significance level.
        
    Returns
    -------
    Tuple[List[float], List[bool]]
        Corrected p-values and a list of booleans indicating significance.
    """
    n = len(p_values)
    if n == 0:
        return [], []
        
    corrected = [p * n for p in p_values]
    # Cap at 1.0
    corrected = [min(p, 1.0) for p in corrected]
    significant = [p < alpha for p in corrected]
    
    return corrected, significant

def permutation_test(x: np.ndarray, y: np.ndarray, n_permutations: int = 1000, seed: int = 42) -> float:
    """
    Perform a permutation test to assess the significance of the correlation between x and y.
    
    Parameters
    ----------
    x : np.ndarray
        First variable.
    y : np.ndarray
        Second variable.
    n_permutations : int
        Number of permutations.
    seed : int
        Random seed.
        
    Returns
    -------
    float
        Empirical p-value.
    """
    np.random.seed(seed)
    n = len(x)
    observed_corr, _ = stats.pearsonr(x, y)
    
    count = 0
    for _ in range(n_permutations):
        perm_y = np.random.permutation(y)
        perm_corr, _ = stats.pearsonr(x, perm_y)
        if abs(perm_corr) >= abs(observed_corr):
            count += 1
            
    return count / n_permutations

def calculate_medes(effect_size: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """
    Calculate Minimum Detectable Effect Size (MDES) for a given sample size.
    (Simplified implementation for Cohen's d context)
    
    Parameters
    ----------
    effect_size : float
        Expected effect size (Cohen's d).
    alpha : float
        Significance level.
    power : float
        Desired statistical power.
        
    Returns
    -------
    int
        Required sample size per group.
    """
    # Approximate formula for two-sample t-test
    # n = 2 * ((Z_alpha + Z_beta) / effect_size)^2
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(np.ceil(n))

def calculate_sample_size_for_r2(r2_target: float, alpha: float = 0.05, power: float = 0.80, n_predictors: int = 6) -> int:
    """
    Estimate sample size needed to detect a target R-squared value.
    
    Parameters
    ----------
    r2_target : float
        Target R-squared value.
    alpha : float
        Significance level.
    power : float
        Desired power.
    n_predictors : int
        Number of predictors in the model.
        
    Returns
    -------
    int
        Required sample size.
    """
    # Approximation using F-test for R-squared
    # f2 = R2 / (1 - R2)
    f2 = r2_target / (1 - r2_target)
    
    # Degrees of freedom
    u = n_predictors
    v = 0 # Will be solved for
    
    # Use G*Power approximation or scipy
    # N = ( (z_alpha + z_beta)^2 ) / f2 + u + 1
    # More precise: use statsmodels or power analysis functions
    # Simplified here:
    
    z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    n = ((z_alpha + z_beta) ** 2) / f2 + u + 1
    return int(np.ceil(n))

def f_test_comparison(r2_full: float, r2_reduced: float, n: int, p_full: int, p_reduced: int) -> float:
    """
    Perform an F-test to compare two nested models.
    
    Parameters
    ----------
    r2_full : float
        R-squared of the full model.
    r2_reduced : float
        R-squared of the reduced model.
    n : int
        Sample size.
    p_full : int
        Number of predictors in full model.
    p_reduced : int
        Number of predictors in reduced model.
        
    Returns
    -------
    float
        p-value of the F-test.
    """
    df1 = p_full - p_reduced
    df2 = n - p_full - 1
    
    f_stat = ((r2_full - r2_reduced) / df1) / ((1 - r2_full) / df2)
    p_value = 1 - stats.f.cdf(f_stat, df1, df2)
    
    return p_value
