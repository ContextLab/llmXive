"""
Statistical helper functions for EEG-RT prediction analysis.

Provides utilities for:
  - Bonferroni correction
  - Permutation tests
  - Power analysis and sample size calculation
  - F-test comparisons
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional
import warnings


def bonferroni_correct(
    p_values: List[float],
    num_tests: Optional[int] = None
) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to multiple p-values.
    
    Args:
        p_values: List of raw p-values
        num_tests: Number of tests (defaults to len(p_values))
        
    Returns:
        Tuple of (corrected p-values, boolean flags for significance at alpha=0.05)
    """
    if num_tests is None:
        num_tests = len(p_values)
    
    if num_tests == 0:
        return [], []
    
    # Bonferroni correction: p_corrected = p_raw * num_tests
    corrected = [min(p * num_tests, 1.0) for p in p_values]
    
    # Significance at alpha = 0.05
    significant = [p < 0.05 for p in corrected]
    
    return corrected, significant


def permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 10000,
    random_state: Optional[int] = None
) -> Tuple[float, float, np.ndarray]:
    """
    Perform permutation test to assess significance of model performance.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        n_permutations: Number of permutations
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (observed statistic, p-value, null distribution)
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    n_samples = len(y)
    
    # Calculate observed statistic (R² from simple linear regression)
    from sklearn.linear_model import LinearRegression
    
    model = LinearRegression()
    model.fit(X, y)
    observed_r2 = model.score(X, y)
    
    # Generate null distribution
    null_distribution = np.zeros(n_permutations)
    
    for i in range(n_permutations):
        # Shuffle y
        y_permuted = np.random.permutation(y)
        
        # Fit model and calculate R²
        model.fit(X, y_permuted)
        null_distribution[i] = model.score(X, y_permuted)
    
    # Calculate p-value (one-tailed: proportion of null >= observed)
    p_value = np.mean(null_distribution >= observed_r2)
    
    return observed_r2, p_value, null_distribution


def calculate_medes(
    effect_size: float,
    power: float = 0.80,
    alpha: float = 0.05,
    num_groups: int = 2
) -> int:
    """
    Calculate Minimum Detectable Effect Size (MDES) for given sample size.
    
    Note: This is a simplified version. For complex designs, use statsmodels.
    
    Args:
        effect_size: Cohen's d or similar effect size metric
        power: Desired statistical power
        alpha: Significance level
        num_groups: Number of groups (for t-test: 2)
        
    Returns:
        Minimum detectable effect size
    """
    # For a two-sample t-test
    if num_groups == 2:
        # Approximate formula for MDES
        # MDES ≈ (z_α/2 + z_β) * √(2/n)
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        
        # This is a simplified approximation
        # For exact calculation, use statsmodels.stats.power
        return (z_alpha + z_beta) * np.sqrt(2)
    
    return effect_size


def calculate_sample_size_for_r2(
    f2: float,
    power: float = 0.80,
    alpha: float = 0.05,
    num_predictors: int = 6
) -> int:
    """
    Calculate required sample size for multiple regression given effect size f².
    
    Uses the non-central F-distribution approach.
    f² = R² / (1 - R²)
    
    Args:
        f2: Cohen's f² effect size
        power: Desired statistical power
        alpha: Significance level
        num_predictors: Number of predictors (k)
        
    Returns:
        Required sample size (n)
    """
    if f2 <= 0:
        raise ValueError("Effect size f² must be positive")
    
    if power <= 0 or power >= 1:
        raise ValueError("Power must be between 0 and 1")
    
    if alpha <= 0 or alpha >= 1:
        raise ValueError("Alpha must be between 0 and 1")
    
    # Degrees of freedom
    df1 = num_predictors
    
    # Binary search for sample size
    n_low = num_predictors + 1
    n_high = 10000  # Upper bound
    
    target_ncp = None
    
    # Find critical F value for given alpha
    # We'll iterate to find n that gives desired power
    
    for n in range(n_low, n_high + 1):
        df2 = n - num_predictors - 1
        
        if df2 <= 0:
            continue
        
        # Non-centrality parameter
        ncp = f2 * n
        
        # Critical F value
        f_critical = stats.f.ppf(1 - alpha, df1, df2)
        
        # Power = P(F > f_critical | ncp)
        power_calculated = 1 - stats.ncf.cdf(f_critical, df1, df2, ncp)
        
        if power_calculated >= power:
            return n
    
    # If we reach here, even n=10000 is not enough
    warnings.warn(
        f"Required sample size exceeds maximum (10000). "
        f"Consider larger effect size or lower power target."
    )
    return n_high


def f_test_comparison(
    r2_reduced: float,
    r2_full: float,
    n: int,
    k_reduced: int,
    k_full: int
) -> Tuple[float, float]:
    """
    Perform F-test to compare nested regression models.
    
    Args:
        r2_reduced: R² of the reduced model
        r2_full: R² of the full model
        n: Sample size
        k_reduced: Number of predictors in reduced model
        k_full: Number of predictors in full model
        
    Returns:
        Tuple of (F-statistic, p-value)
    """
    if r2_full == r2_reduced:
        return 0.0, 1.0
    
    if n <= k_full + 1:
        raise ValueError("Sample size must be greater than number of predictors + 1")
    
    # F-statistic
    # F = [(R²_full - R²_reduced) / (k_full - k_reduced)] / 
    #     [(1 - R²_full) / (n - k_full - 1)]
    
    numerator = (r2_full - r2_reduced) / (k_full - k_reduced)
    denominator = (1 - r2_full) / (n - k_full - 1)
    
    if denominator == 0:
        return float('inf'), 0.0
    
    f_stat = numerator / denominator
    
    # Degrees of freedom
    df1 = k_full - k_reduced
    df2 = n - k_full - 1
    
    # p-value
    p_value = 1 - stats.f.cdf(f_stat, df1, df2)
    
    return f_stat, p_value
