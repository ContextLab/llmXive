"""
Metric calculation and statistical testing utilities.
"""
import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Union
import logging

logger = logging.getLogger("utils.metrics")

def calculate_mse(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """Calculate Mean Squared Error."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return float(np.mean((y_true - y_pred) ** 2))

def calculate_mae(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """Calculate Mean Absolute Error."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))

def calculate_pearson_r(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """Calculate Pearson correlation coefficient."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    r, _ = stats.pearsonr(y_true, y_pred)
    return float(r)

def paired_t_test(errors1: Union[List[float], np.ndarray], errors2: Union[List[float], np.ndarray]) -> Tuple[float, float]:
    """
    Perform a paired t-test on two sets of errors.
    
    Args:
        errors1: First set of errors.
        errors2: Second set of errors.
        
    Returns:
        Tuple of (t-statistic, p-value).
    """
    errors1 = np.array(errors1)
    errors2 = np.array(errors2)
    t_stat, p_val = stats.ttest_rel(errors1, errors2)
    return float(t_stat), float(p_val)

def wilcoxon_signed_rank_test(errors1: Union[List[float], np.ndarray], errors2: Union[List[float], np.ndarray]) -> Tuple[float, float]:
    """
    Perform a Wilcoxon signed-rank test on two sets of errors.
    
    Args:
        errors1: First set of errors.
        errors2: Second set of errors.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    errors1 = np.array(errors1)
    errors2 = np.array(errors2)
    stat, p_val = stats.wilcoxon(errors1, errors2)
    return float(stat), float(p_val)

def evaluate_model(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Evaluate model performance with multiple metrics.
    
    Args:
        y_true: True values.
        y_pred: Predicted values.
        
    Returns:
        Dictionary of metrics.
    """
    return {
        "mse": calculate_mse(y_true, y_pred),
        "mae": calculate_mae(y_true, y_pred),
        "pearson_r": calculate_pearson_r(y_true, y_pred)
    }

def compare_models(y_true: Union[List[float], np.ndarray], y_pred1: Union[List[float], np.ndarray], y_pred2: Union[List[float], np.ndarray]) -> Dict[str, Any]:
    """
    Compare two models using paired t-test and Wilcoxon test.
    
    Args:
        y_true: True values.
        y_pred1: Predictions from model 1.
        y_pred2: Predictions from model 2.
        
    Returns:
        Dictionary with comparison results.
    """
    errors1 = np.abs(np.array(y_true) - np.array(y_pred1))
    errors2 = np.abs(np.array(y_true) - np.array(y_pred2))
    
    t_stat, t_pval = paired_t_test(errors1, errors2)
    w_stat, w_pval = wilcoxon_signed_rank_test(errors1, errors2)
    
    return {
        "paired_t_test": {"t_statistic": t_stat, "p_value": t_pval},
        "wilcoxon_test": {"statistic": w_stat, "p_value": w_pval},
        "model1_mae": float(np.mean(errors1)),
        "model2_mae": float(np.mean(errors2))
    }

if __name__ == "__main__":
    # Test
    y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_pred1 = [1.1, 2.1, 2.9, 4.2, 4.8]
    y_pred2 = [1.2, 2.2, 2.8, 4.1, 4.9]
    
    metrics = evaluate_model(y_true, y_pred1)
    print(f"Metrics: {metrics}")
    
    comparison = compare_models(y_true, y_pred1, y_pred2)
    print(f"Comparison: {comparison}")