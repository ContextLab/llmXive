import numpy as np
import pandas as pd
from typing import Tuple, List
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import Ridge
import json

def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> dict:
    """
    Compute Pearson correlation and RMSE.
    
    Args:
        y_true: True labels.
        y_pred: Predicted labels.
        
    Returns:
        Dictionary with metrics.
    """
    r, p_value = pearsonr(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    return {
        'pearson_r': float(r),
        'p_value': float(p_value),
        'rmse': float(rmse),
        'r2': float(r2)
    }

def compare_with_baseline(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_mean_baseline: np.ndarray
) -> dict:
    """
    Compare model performance against a mean-baseline predictor.
    
    Args:
        y_true: True labels.
        y_pred: Model predictions.
        y_mean_baseline: Mean-baseline predictions (mean of y_true).
        
    Returns:
        Dictionary with comparison metrics.
    """
    model_metrics = compute_metrics(y_true, y_pred)
    baseline_metrics = compute_metrics(y_true, y_mean_baseline)
    
    improvement_r2 = model_metrics['r2'] - baseline_metrics['r2']
    
    return {
        'model_metrics': model_metrics,
        'baseline_metrics': baseline_metrics,
        'r2_improvement': float(improvement_r2),
        'better_than_baseline': improvement_r2 > 0
    }

def bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to channel-wise correlations.
    
    Args:
        p_values: List of p-values.
        alpha: Significance level.
        
    Returns:
        Tuple of (adjusted_p_values, significant_flags).
    """
    n_tests = len(p_values)
    adjusted_p = [p * n_tests for p in p_values]
    # Cap at 1.0
    adjusted_p = [min(p, 1.0) for p in adjusted_p]
    significant = [p < alpha for p in adjusted_p]
    
    return adjusted_p, significant

def permutation_test(
    model: Ridge,
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    random_state: int = 42
) -> float:
    """
    Perform permutation testing for global significance.
    
    Args:
        model: Trained model.
        X: Features.
        y: Labels.
        n_permutations: Number of permutations.
        random_state: Random seed.
        
    Returns:
        p-value for the observed correlation.
    """
    np.random.seed(random_state)
    
    # Observed correlation
    y_pred = model.predict(X)
    r_obs, _ = pearsonr(y, y_pred)
    
    # Permutation distribution
    r_perm = []
    for _ in range(n_permutations):
        y_perm = np.random.permutation(y)
        model_perm = Ridge(alpha=model.alpha)
        model_perm.fit(X, y_perm)
        y_pred_perm = model_perm.predict(X)
        r_p, _ = pearsonr(y_perm, y_pred_perm)
        r_perm.append(r_p)
    
    # Calculate p-value
    r_perm = np.array(r_perm)
    p_value = np.mean(np.abs(r_perm) >= np.abs(r_obs))
    
    return float(p_value)

def save_metrics(
    metrics: dict,
    output_path: str
):
    """
    Save metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics.
        output_path: Path to output file.
    """
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    print("Evaluation module loaded successfully.")
