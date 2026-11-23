"""
Statistical helper functions for the EEG analysis pipeline.
Includes Bonferroni correction, permutation tests, MDES, and sample size calculations.
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional
import warnings

def bonferroni_correct(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level.
        
    Returns:
        Tuple of (corrected p-values, list of booleans indicating significance).
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return [], []
    
    corrected_p = [min(p * n_tests, 1.0) for p in p_values]
    significant = [p < (alpha / n_tests) for p in p_values]
    
    return corrected_p, significant

def permutation_test(
    X: np.ndarray, 
    y: np.ndarray, 
    n_permutations: int = 10000, 
    seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Perform a permutation test to assess the significance of a correlation/regression.
    
    Args:
        X: Feature matrix (n_samples, n_features).
        y: Target vector (n_samples,).
        n_permutations: Number of permutations.
        seed: Random seed.
        
    Returns:
        Dict with 'observed_r2', 'p_value', 'null_distribution_mean', 'null_distribution_std'.
    """
    if seed is not None:
        np.random.seed(seed)
        
    n_samples = X.shape[0]
    k_features = X.shape[1]
    
    # Fit model on original data (simplified R2 calculation for permutation context)
    # Using OLS R2: 1 - SS_res / SS_tot
    # We need a simple regression implementation here or use sklearn if available.
    # To keep dependencies minimal and robust, we use numpy for simple linear regression logic.
    # However, for multivariate X, we need a proper solver.
    # Assuming sklearn is available as per requirements.txt.
    try:
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        observed_r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    except ImportError:
        raise ImportError("scikit-learn is required for permutation tests.")
    
    null_r2s = []
    for _ in range(n_permutations):
        y_perm = np.random.permutation(y)
        model.fit(X, y_perm)
        y_pred_perm = model.predict(X)
        ss_res_perm = np.sum((y_perm - y_pred_perm) ** 2)
        ss_tot_perm = np.sum((y_perm - np.mean(y_perm)) ** 2)
        r2_perm = 1 - (ss_res_perm / ss_tot_perm) if ss_tot_perm > 0 else 0.0
        null_r2s.append(r2_perm)
        
    null_r2s = np.array(null_r2s)
    p_value = np.mean(null_r2s >= observed_r2)
    
    return {
        'observed_r2': observed_r2,
        'p_value': p_value,
        'null_distribution_mean': float(np.mean(null_r2s)),
        'null_distribution_std': float(np.std(null_r2s))
    }

def calculate_medes(
    effect_size: float, 
    alpha: float = 0.05, 
    power: float = 0.80, 
    test_type: str = "t-test"
) -> int:
    """
    Calculate Minimum Detectable Effect Size (MDES) or required sample size.
    For this project, we focus on sample size for a given effect size.
    """
    # Placeholder for specific MDES logic if needed.
    # Currently, we use calculate_sample_size_for_r2 directly.
    raise NotImplementedError("Use calculate_sample_size_for_r2 for regression power analysis.")

def calculate_sample_size_for_r2(
    effect_size_f2: float, 
    alpha: float = 0.05, 
    power: float = 0.80, 
    k: int = 6
) -> int:
    """
    Calculate the required sample size (N) for a multiple regression model
    to achieve a target power for a given effect size (f2).
    
    Args:
        effect_size_f2: Cohen's f2 (R2 / (1 - R2)).
        alpha: Significance level.
        power: Desired statistical power.
        k: Number of predictors.
        
    Returns:
        Required sample size N.
    """
    try:
        from statsmodels.stats.power import FTestPower
    except ImportError:
        raise ImportError("statsmodels is required for power analysis. Add it to requirements.txt.")
    
    ftest = FTestPower()
    
    # Calculate degrees of freedom
    # df_num = k (number of predictors)
    # df_denom = N - k - 1
    # We need to solve for N such that power = desired_power
    # statsmodels FTestPower.solve_power handles this.
    
    nobs = ftest.solve_power(
        effect_size=effect_size_f2,
        nobs1=None, # We are solving for nobs
        alpha=alpha,
        power=power,
        df_num=k,
        ratio=1.0 # Ratio of sample sizes (1 for single sample case in regression context)
    )
    
    if nobs is None:
        # Fallback or error if solution not found
        warnings.warn("Could not compute sample size for given parameters.")
        return -1
        
    return int(np.ceil(nobs))

def f_test_comparison(
    r2_reduced: float, 
    r2_full: float, 
    n: int, 
    k_reduced: int, 
    k_full: int
) -> Tuple[float, float]:
    """
    Perform an F-test to compare two nested models.
    
    Args:
        r2_reduced: R-squared of the reduced model.
        r2_full: R-squared of the full model.
        n: Number of samples.
        k_reduced: Number of predictors in reduced model.
        k_full: Number of predictors in full model.
        
    Returns:
        Tuple of (F-statistic, p-value).
    """
    df_num = k_full - k_reduced
    df_denom = n - k_full - 1
    
    if df_denom <= 0:
        return 0.0, 1.0
        
    f_stat = ((r2_full - r2_reduced) / df_num) / ((1 - r2_full) / df_denom)
    p_val = 1 - stats.f.cdf(f_stat, df_num, df_denom)
    
    return f_stat, p_val
