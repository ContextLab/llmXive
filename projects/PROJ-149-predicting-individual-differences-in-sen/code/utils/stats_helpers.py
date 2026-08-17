"""
Statistical helper functions for EEG analysis pipeline.
Includes power analysis utilities, permutation tests, and effect size calculations.
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional
import warnings
from statsmodels.stats.power import FTestAnovaPower


def bonferroni_correct(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default 0.05)
        
    Returns:
        Tuple of (corrected_p_values, significant_flags)
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return [], []
    
    # Bonferroni correction: alpha / n_tests
    corrected_alpha = alpha / n_tests
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]
    significant_flags = [p < corrected_alpha for p in corrected_p_values]
    
    return corrected_p_values, significant_flags


def permutation_test(
    X: np.ndarray, 
    y: np.ndarray, 
    n_permutations: int = 10000, 
    random_state: Optional[int] = None
) -> Tuple[float, np.ndarray]:
    """
    Perform a permutation test to assess significance of a relationship.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        n_permutations: Number of permutations
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (observed_statistic, null_distribution)
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
        model.fit(X, y_permuted)
        null_distribution[i] = model.score(X, y_permuted)
    
    return observed_r2, null_distribution


def calculate_medes(
    effect_size: float, 
    alpha: float = 0.05, 
    power: float = 0.80,
    n_groups: int = 2
) -> int:
    """
    Calculate Minimum Detectable Effect Size (MDES) for a given sample size.
    
    Args:
        effect_size: Expected effect size (Cohen's d or f²)
        alpha: Significance level
        power: Desired statistical power
        n_groups: Number of groups (for ANOVA)
        
    Returns:
        Minimum required sample size per group
    """
    # Use statsmodels for power calculation
    from statsmodels.stats.power import TTestIndPower, FTestAnovaPower
    
    if n_groups == 2:
        analyzer = TTestIndPower()
        n = analyzer.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            ratio=1.0
        )
    else:
        analyzer = FTestAnovaPower()
        n = analyzer.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            n_groups=n_groups,
            ratio=1.0
        )
    
    return int(np.ceil(n))


def calculate_sample_size_for_r2(
    target_r2: float,
    n_predictors: int,
    alpha: float = 0.05,
    power: float = 0.80
) -> int:
    """
    Calculate required sample size to detect a target R² effect size.
    
    Args:
        target_r2: Target R² value (0 to 1)
        n_predictors: Number of predictors in the model
        alpha: Significance level
        power: Desired statistical power
        
    Returns:
        Required sample size
    """
    # Convert R² to f² (Cohen's f²)
    # f² = R² / (1 - R²)
    if target_r2 >= 1.0:
        target_r2 = 0.99  # Avoid division by zero
    
    effect_size_f2 = target_r2 / (1 - target_r2)
    
    # Use F-test power analysis
    analyzer = FTestAnovaPower()
    
    try:
        # For regression, n_groups=1 is used as a placeholder
        # The actual calculation accounts for predictors through effect size
        required_n = analyzer.solve_power(
            effect_size=effect_size_f2,
            alpha=alpha,
            power=power,
            n_groups=1,
            ratio=1.0
        )
        
        # Adjust for number of predictors (rough approximation)
        # More predictors typically require larger samples
        adjusted_n = required_n * (1 + n_predictors / 10)
        
        return int(np.ceil(adjusted_n))
        
    except Exception as e:
        warnings.warn(f"Power calculation failed: {e}. Using fallback estimate.")
        # Fallback: rule of thumb (10-20 samples per predictor)
        return max(30, n_predictors * 20)


def f_test_comparison(
    r2_reduced: float,
    r2_full: float,
    n_predictors_reduced: int,
    n_predictors_full: int,
    n_samples: int
) -> Tuple[float, float]:
    """
    Perform F-test to compare two nested models.
    
    Args:
        r2_reduced: R² of the reduced model
        r2_full: R² of the full model
        n_predictors_reduced: Number of predictors in reduced model
        n_predictors_full: Number of predictors in full model
        n_samples: Number of samples
        
    Returns:
        Tuple of (F-statistic, p-value)
    """
    # F = [(R²_full - R²_reduced) / (df_full - df_reduced)] / [(1 - R²_full) / df_error]
    # df_full - df_reduced = n_predictors_full - n_predictors_reduced
    # df_error = n_samples - n_predictors_full - 1
    
    numerator = (r2_full - r2_reduced) / (n_predictors_full - n_predictors_reduced)
    denominator = (1 - r2_full) / (n_samples - n_predictors_full - 1)
    
    if denominator == 0:
        return 0.0, 1.0
    
    f_stat = numerator / denominator
    df1 = n_predictors_full - n_predictors_reduced
    df2 = n_samples - n_predictors_full - 1
    
    p_value = 1 - stats.f.cdf(f_stat, df1, df2)
    
    return f_stat, p_value
