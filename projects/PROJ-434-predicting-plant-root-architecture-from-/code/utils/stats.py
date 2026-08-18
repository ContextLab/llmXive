"""
Statistical utilities for the research pipeline.
Includes permutation tests and baseline R² calculation.
"""
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error
from typing import Callable, Tuple, Optional, Union
import warnings

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    """Calculate R² and RMSE."""
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return r2, rmse

def calculate_baseline_r2(y_train: np.ndarray, y_test: np.ndarray) -> float:
    """
    Calculate the baseline R² for a mean-prediction model.
    The model predicts the mean of the training set for all test samples.
    R² = 1 - (SS_res / SS_tot)
    where SS_res = sum((y_test - mean(y_train))**2)
    and SS_tot = sum((y_test - mean(y_test))**2)
    """
    if len(y_train) == 0 or len(y_test) == 0:
        warnings.warn("Empty train or test set provided to baseline R² calculation.")
        return 0.0
    
    mean_train = np.mean(y_train)
    y_pred_baseline = np.full_like(y_test, mean_train, dtype=float)
    
    ss_res = np.sum((y_test - y_pred_baseline) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    
    if ss_tot == 0:
        return 0.0
    
    return 1 - (ss_res / ss_tot)

def delta_r2(observed_r2: float, baseline_r2: float) -> float:
    """Calculate the improvement over the baseline."""
    return observed_r2 - baseline_r2

def permutation_test(
    X: np.ndarray, 
    y: np.ndarray, 
    model_fn: Callable, 
    n_iterations: int = 1000, 
    random_state: Optional[int] = None
) -> float:
    """
    Perform a permutation test to assess feature importance.
    Permutes the target variable y and calculates the distribution of R² scores.
    Returns the p-value: proportion of permuted R² >= observed R².
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    # Train model on original data
    model = model_fn(X, y)
    y_pred = model.predict(X)
    observed_r2 = r2_score(y, y_pred)
    
    permuted_r2s = []
    for _ in range(n_iterations):
        y_perm = np.random.permutation(y)
        model_perm = model_fn(X, y_perm)
        y_pred_perm = model_perm.predict(X)
        r2_perm = r2_score(y, y_pred_perm) # Compare against original y
        permuted_r2s.append(r2_perm)
    
    p_value = np.mean(np.array(permuted_r2s) >= observed_r2)
    return p_value

def stratified_permutation_test(
    X: np.ndarray, 
    y: np.ndarray, 
    groups: np.ndarray, 
    model_fn: Callable, 
    n_iterations: int = 1000, 
    random_state: Optional[int] = None
) -> float:
    """
    Perform a stratified permutation test where shuffling is done within groups.
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    model = model_fn(X, y)
    y_pred = model.predict(X)
    observed_r2 = r2_score(y, y_pred)
    
    permuted_r2s = []
    unique_groups = np.unique(groups)
    
    for _ in range(n_iterations):
        y_perm = y.copy()
        for g in unique_groups:
            mask = groups == g
            y_perm[mask] = np.random.permutation(y[mask])
        
        model_perm = model_fn(X, y_perm)
        y_pred_perm = model_perm.predict(X)
        r2_perm = r2_score(y, y_pred_perm)
        permuted_r2s.append(r2_perm)
    
    p_value = np.mean(np.array(permuted_r2s) >= observed_r2)
    return p_value
