"""
Statistical utilities for the crack propagation prediction pipeline.
"""
import numpy as np
from typing import Callable, Optional, Tuple, List
from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression

def null_model_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R² score for a null model (intercept-only).
    
    Args:
        y_true: True target values
        y_pred: Predicted target values (should be constant for null model)
        
    Returns:
        R² score
    """
    return r2_score(y_true, y_pred)

def compare_models_r2(model1_r2: float, model2_r2: float) -> float:
    """
    Calculate the difference in R² between two models.
    
    Args:
        model1_r2: R² score of first model
        model2_r2: R² score of second model
        
    Returns:
        Difference in R² (model2 - model1)
    """
    return model2_r2 - model1_r2

def permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    model_func: Callable,
    n_permutations: int = 1000,
    random_seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    Perform a permutation test to assess model significance.
    
    Args:
        X: Feature matrix
        y: Target vector
        model_func: Function that takes (X, y) and returns R² score
        n_permutations: Number of permutations
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (observed R², p-value)
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Calculate observed R²
    observed_r2 = model_func(X, y)
    
    # Permutation test
    permuted_scores = []
    for _ in range(n_permutations):
        y_permuted = np.random.permutation(y)
        permuted_r2 = model_func(X, y_permuted)
        permuted_scores.append(permuted_r2)
    
    # Calculate p-value
    p_value = np.mean(np.array(permuted_scores) >= observed_r2)
    
    return observed_r2, p_value

def permutation_test_model_comparison(
    X: np.ndarray,
    y: np.ndarray,
    model1_func: Callable,
    model2_func: Callable,
    n_permutations: int = 1000,
    random_seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    Perform a permutation test to compare two models.
    
    Args:
        X: Feature matrix
        y: Target vector
        model1_func: Function for first model (returns R²)
        model2_func: Function for second model (returns R²)
        n_permutations: Number of permutations
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (observed ΔR², p-value)
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Calculate observed ΔR²
    r2_1 = model1_func(X, y)
    r2_2 = model2_func(X, y)
    observed_delta_r2 = r2_2 - r2_1
    
    # Permutation test
    permuted_deltas = []
    for _ in range(n_permutations):
        y_permuted = np.random.permutation(y)
        r2_1_perm = model1_func(X, y_permuted)
        r2_2_perm = model2_func(X, y_permuted)
        permuted_delta = r2_2_perm - r2_1_perm
        permuted_deltas.append(permuted_delta)
    
    # Calculate p-value
    p_value = np.mean(np.array(permuted_deltas) >= observed_delta_r2)
    
    return observed_delta_r2, p_value
