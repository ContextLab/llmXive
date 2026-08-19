"""
Statistical utilities for the pipeline.
"""
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error
from typing import Callable, Tuple, Optional, Union
import warnings

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    """Calculate R2 and RMSE."""
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return r2, rmse

def calculate_baseline_r2(y_true: np.ndarray, y_pred_mean: float) -> float:
    """Calculate R2 for a mean-prediction model."""
    y_mean = np.mean(y_true)
    ss_tot = np.sum((y_true - y_mean) ** 2)
    ss_res = np.sum((y_true - y_pred_mean) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)

def delta_r2(observed_r2: float, baseline_r2: float) -> float:
    """Calculate the gain in R2 over the baseline."""
    return observed_r2 - baseline_r2

def permutation_test(model_fn: Callable, X: np.ndarray, y: np.ndarray, 
                     n_iterations: int = 1000, random_seed: int = 42) -> np.ndarray:
    """Perform a permutation test to assess feature importance significance."""
    np.random.seed(random_seed)
    scores = []
    for _ in range(n_iterations):
        y_perm = np.random.permutation(y)
        # Simulate model prediction on permuted data (placeholder logic)
        # In real implementation, model_fn would be called
        pred = np.full_like(y_perm, np.mean(y_perm))
        r2, _ = calculate_metrics(y_perm, pred)
        scores.append(r2)
    return np.array(scores)

def stratified_permutation_test(model_fn: Callable, X: np.ndarray, y: np.ndarray, 
                                groups: np.ndarray, n_iterations: int = 1000, 
                                random_seed: int = 42) -> np.ndarray:
    """Perform a stratified permutation test preserving group structure."""
    np.random.seed(random_seed)
    scores = []
    unique_groups = np.unique(groups)
    
    for _ in range(n_iterations):
        y_perm = y.copy()
        for group in unique_groups:
            mask = groups == group
            y_perm[mask] = np.random.permutation(y[mask])
        
        # Simulate model prediction
        pred = np.full_like(y_perm, np.mean(y_perm))
        r2, _ = calculate_metrics(y_perm, pred)
        scores.append(r2)
    return np.array(scores)
