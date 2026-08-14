"""
Statistical helper functions for the EEG analysis pipeline.

Provides utilities for:
- Bonferroni correction
- Permutation tests
- Power analysis (MDES, sample size calculation)
- F-test comparisons
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional
import warnings

def bonferroni_correct(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default 0.05)
        
    Returns:
        Tuple of (adjusted p-values, boolean significance flags)
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return [], []
    
    adjusted_p_values = [min(p * n_tests, 1.0) for p in p_values]
    significant = [p < (alpha / n_tests) for p in p_values]
    
    return adjusted_p_values, significant

def permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    statistic: callable,
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[float, float, np.ndarray]:
    """
    Perform a permutation test for a given statistic.
    
    Args:
        X: Predictor matrix (n_samples, n_features)
        y: Outcome vector (n_samples,)
        statistic: Function that computes the statistic of interest (e.g., R²)
        n_permutations: Number of permutations (default 1000)
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (observed statistic, p-value, null distribution)
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    n_samples = len(y)
    observed_stat = statistic(X, y)
    
    null_distribution = np.zeros(n_permutations)
    for i in range(n_permutations):
        y_permuted = np.random.permutation(y)
        null_distribution[i] = statistic(X, y_permuted)
    
    # Calculate p-value (two-tailed)
    p_value = np.mean(np.abs(null_distribution) >= np.abs(observed_stat))
    
    return observed_stat, p_value, null_distribution

def calculate_medes(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
    test_type: str = "t-test"
) -> int:
    """
    Calculate Minimum Detectable Effect Size (MDES).
    
    Args:
        effect_size: Expected effect size (Cohen's d for t-test, f² for regression)
        alpha: Significance level
        power: Desired statistical power
        test_type: Type of test ("t-test", "regression", etc.)
        
    Returns:
        Minimum sample size required
    """
    if test_type == "t-test":
        # Using scipy's power analysis approximation
        # n = 2 * (Z_alpha + Z_beta)^2 / d^2
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        n = 2 * ((z_alpha + z_beta) ** 2) / (effect_size ** 2)
        return int(np.ceil(n))
    
    elif test_type == "regression":
        # For regression, effect_size is f²
        # n = (L / f²) + u + 1
        # L depends on alpha and power
        # Approximate L for alpha=0.05, power=0.80
        L = 7.85
        u = 1 # Number of predictors (simplified)
        n = (L / effect_size) + u + 1
        return int(np.ceil(n))
    
    else:
        raise ValueError(f"Unsupported test type: {test_type}")

def calculate_sample_size_for_r2(
    effect_size_f2: float,
    alpha: float = 0.05,
    power: float = 0.80,
    num_predictors: int = 6
) -> int:
    """
    Calculate the required sample size for a multiple regression given a target R².
    
    Effect size f² = R² / (1 - R²)
    
    Args:
        effect_size_f2: Cohen's f² effect size
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
        num_predictors: Number of predictors (k)
        
    Returns:
        Required sample size (n)
    """
    # Using the approximation from Cohen (1988)
    # n = (L / f²) + u + 1
    # where L is the non-centrality parameter based on alpha and power
    # For alpha=0.05, power=0.80, L ≈ 7.85
    
    # More precise calculation using non-central F distribution if statsmodels is available
    try:
        from statsmodels.stats.power import FTestPower
        ftest = FTestPower()
        n = ftest.solve_power(
            effect_size=effect_size_f2,
            alpha=alpha,
            power=power,
            nobs1=None,
            df_num=num_predictors
        )
        return int(np.ceil(n))
    except ImportError:
        # Fallback to Cohen's approximation
        L = 7.85 # Approximate for alpha=0.05, power=0.80
        n = (L / effect_size_f2) + num_predictors + 1
        return int(np.ceil(n))

def f_test_comparison(
    r2_reduced: float,
    r2_full: float,
    n: int,
    k_reduced: int,
    k_full: int
) -> Tuple[float, float]:
    """
    Perform an F-test to compare two nested regression models.
    
    Args:
        r2_reduced: R² of the reduced model
        r2_full: R² of the full model
        n: Sample size
        k_reduced: Number of predictors in reduced model
        k_full: Number of predictors in full model
        
    Returns:
        Tuple of (F-statistic, p-value)
    """
    # F = ((R²_full - R²_reduced) / (k_full - k_reduced)) / ((1 - R²_full) / (n - k_full - 1))
    df1 = k_full - k_reduced
    df2 = n - k_full - 1
    
    if df2 <= 0:
        raise ValueError("Sample size too small for F-test with given predictors.")
    
    numerator = (r2_full - r2_reduced) / df1
    denominator = (1 - r2_full) / df2
    
    if denominator == 0:
        return float('inf'), 0.0
    
    f_stat = numerator / denominator
    p_value = 1 - stats.f.cdf(f_stat, df1, df2)
    
    return f_stat, p_value