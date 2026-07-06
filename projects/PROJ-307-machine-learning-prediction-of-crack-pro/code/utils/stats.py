"""
Statistical utilities including permutation tests.

This module provides functions for calculating R-squared metrics,
comparing model performance, and performing permutation tests to
assess statistical significance of model improvements.
"""
import numpy as np
from typing import Callable, Optional, Tuple, List
from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression

def null_model_r2(y: np.ndarray) -> float:
    """
    Calculate R2 for an intercept-only (mean) model.
    
    The null model predicts the mean of y for all observations.
    R2 = 1 - SS_res / SS_tot
    For the null model, SS_res = SS_tot, so R2 = 0.0 by definition.
    
    Args:
        y: Target values (1D array).
        
    Returns:
        R2 score for the null model (always 0.0).
    """
    return 0.0

def compare_models_r2(model1_r2: float, model2_r2: float) -> float:
    """
    Calculate the difference in R2 between two models.
    
    Args:
        model1_r2: R2 score of the baseline/reduced model.
        model2_r2: R2 score of the augmented/full model.
        
    Returns:
        Delta R2 = model2_r2 - model1_r2.
        Positive values indicate improvement by model2.
    """
    return model2_r2 - model1_r2

def permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    seed: Optional[int] = None,
    metric: Callable[[np.ndarray, np.ndarray], float] = r2_score
) -> Tuple[float, float]:
    """
    Perform a permutation test to assess the significance of a model's performance.
    
    This function tests the null hypothesis that there is no relationship between
    features X and target y. It does this by randomly permuting y values and
    recalculating the model performance metric.
    
    **Null Hypothesis**: Target values are randomly permuted (no relationship between X and y).
    **Test Statistic**: The observed metric value (e.g., R2) from the model trained on original data.
    **P-value**: Proportion of permuted statistics >= observed statistic.
    
    For R2 specifically:
    - Observed Statistic: R2 of the full model on original data.
    - Null Distribution: R2 of models trained on permuted y values.
    - P-value: Fraction of permuted R2 values >= observed R2.
    
    Args:
        X: Feature matrix (2D array).
        y: Target vector (1D array).
        n_permutations: Number of permutations to perform.
        seed: Random seed for reproducibility.
        metric: Scoring function. Default is sklearn's r2_score.
                For R2, higher is better.
                
    Returns:
        Tuple of (observed_stat, p_value):
            observed_stat: The metric value on the original (unpermuted) data.
            p_value: The proportion of permuted metrics >= observed_stat.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Calculate observed statistic on original data
    # Use a simple LinearRegression as the baseline model for the test
    base_model = LinearRegression()
    base_model.fit(X, y)
    y_pred = base_model.predict(X)
    observed_stat = metric(y, y_pred)
    
    # Generate null distribution by permuting y
    perm_stats = []
    for _ in range(n_permutations):
        y_perm = np.random.permutation(y)
        base_model_perm = LinearRegression()
        base_model_perm.fit(X, y_perm)
        y_pred_perm = base_model_perm.predict(X)
        perm_stat = metric(y_perm, y_pred_perm)
        perm_stats.append(perm_stat)
    
    perm_stats = np.array(perm_stats)
    
    # Calculate p-value: proportion of permuted stats >= observed stat
    # For R2, we expect most permuted R2 to be near 0 or negative.
    # If the model is significant, observed_stat should be much higher.
    p_value = np.sum(perm_stats >= observed_stat) / n_permutations
    
    return observed_stat, p_value

def permutation_test_model_comparison(
    X: np.ndarray,
    y: np.ndarray,
    model_full: Callable,
    model_reduced: Callable,
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    Perform a permutation test comparing two nested models.
    
    This tests whether the additional features in model_full significantly
    improve performance over model_reduced.
    
    **Null Hypothesis**: The additional features in model_full provide no
    predictive power beyond model_reduced.
    **Test Statistic**: Difference in R2 between full and reduced models on original data.
    **P-value**: Proportion of permuted differences >= observed difference.
    
    Args:
        X: Feature matrix for the full model.
        y: Target vector.
        model_full: A callable that takes (X, y) and returns an R2 score.
                    Example: lambda X, y: r2_score(y, LinearRegression().fit(X, y).predict(X))
        model_reduced: A callable that takes (X_reduced, y) and returns an R2 score.
                       X_reduced should be a subset of columns from X.
        n_permutations: Number of permutations.
        seed: Random seed.
        
    Returns:
        Tuple of (observed_stat, p_value):
            observed_stat: Delta R2 (full - reduced) on original data.
            p_value: Probability of observing such a delta under the null.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Calculate observed statistic
    r2_full = model_full(X, y)
    # Assume reduced model uses first k features (adjust as needed)
    # For this generic implementation, we'll assume reduced uses a subset
    # In practice, the caller should pass the correct reduced feature set
    # For now, we'll use a simple approach: reduced uses first half of features
    n_features = X.shape[1]
    if n_features < 2:
        raise ValueError("Permutation test for model comparison requires at least 2 features.")
    X_reduced = X[:, :n_features//2]
    r2_reduced = model_reduced(X_reduced, y)
    
    observed_stat = r2_full - r2_reduced
    
    # Generate null distribution
    perm_stats = []
    for _ in range(n_permutations):
        y_perm = np.random.permutation(y)
        
        r2_full_perm = model_full(X, y_perm)
        r2_reduced_perm = model_reduced(X_reduced, y_perm)
        
        perm_stat = r2_full_perm - r2_reduced_perm
        perm_stats.append(perm_stat)
    
    perm_stats = np.array(perm_stats)
    
    # P-value: proportion of permuted stats >= observed stat
    p_value = np.sum(perm_stats >= observed_stat) / n_permutations
    
    return observed_stat, p_value