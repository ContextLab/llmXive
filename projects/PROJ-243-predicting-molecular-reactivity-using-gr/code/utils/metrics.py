"""
Metric calculation and statistical testing utilities.

This module provides the single source of truth for all statistical tests
required by the project, specifically:
- MSE, MAE, Pearson R for model evaluation
- Wilcoxon signed-rank test (PRIMARY per Plan.md)
- Paired t-test (SENSITIVITY per Plan.md)
"""
import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Union
import logging

logger = logging.getLogger("utils.metrics")

def calculate_mse(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Mean Squared Error.
    
    Args:
        y_true: True values.
        y_pred: Predicted values.
        
    Returns:
        Mean Squared Error as a float.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Input shapes must match: {y_true.shape} vs {y_pred.shape}")
        
    return float(np.mean((y_true - y_pred) ** 2))

def calculate_mae(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Mean Absolute Error.
    
    Args:
        y_true: True values.
        y_pred: Predicted values.
        
    Returns:
        Mean Absolute Error as a float.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Input shapes must match: {y_true.shape} vs {y_pred.shape}")
        
    return float(np.mean(np.abs(y_true - y_pred)))

def calculate_pearson_r(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Pearson correlation coefficient.
    
    Args:
        y_true: True values.
        y_pred: Predicted values.
        
    Returns:
        Pearson correlation coefficient as a float.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Input shapes must match: {y_true.shape} vs {y_pred.shape}")
        
    if len(y_true) < 2:
        raise ValueError("Pearson correlation requires at least 2 data points.")
        
    r, _ = stats.pearsonr(y_true, y_pred)
    return float(r)

def paired_t_test(errors1: Union[List[float], np.ndarray], errors2: Union[List[float], np.ndarray]) -> Tuple[float, float]:
    """
    Perform a paired t-test on two sets of errors.
    
    This is the SENSITIVITY test per Plan.md.
    
    Args:
        errors1: First set of errors (e.g., absolute errors from model 1).
        errors2: Second set of errors (e.g., absolute errors from model 2).
        
    Returns:
        Tuple of (t-statistic, p-value).
    """
    errors1 = np.array(errors1, dtype=float)
    errors2 = np.array(errors2, dtype=float)
    
    if errors1.shape != errors2.shape:
        raise ValueError(f"Error arrays must have the same shape: {errors1.shape} vs {errors2.shape}")
        
    if len(errors1) < 2:
        raise ValueError("Paired t-test requires at least 2 data points.")
        
    t_stat, p_val = stats.ttest_rel(errors1, errors2)
    logger.debug(f"Paired t-test: t={t_stat:.4f}, p={p_val:.4f}")
    return float(t_stat), float(p_val)

def wilcoxon_signed_rank_test(errors1: Union[List[float], np.ndarray], errors2: Union[List[float], np.ndarray]) -> Tuple[float, float]:
    """
    Perform a Wilcoxon signed-rank test on two sets of errors.
    
    This is the PRIMARY test per Plan.md.
    
    Args:
        errors1: First set of errors (e.g., absolute errors from model 1).
        errors2: Second set of errors (e.g., absolute errors from model 2).
        
    Returns:
        Tuple of (statistic, p-value).
    """
    errors1 = np.array(errors1, dtype=float)
    errors2 = np.array(errors2, dtype=float)
    
    if errors1.shape != errors2.shape:
        raise ValueError(f"Error arrays must have the same shape: {errors1.shape} vs {errors2.shape}")
        
    if len(errors1) < 2:
        raise ValueError("Wilcoxon test requires at least 2 data points.")
        
    # Handle cases where differences are exactly zero (stats.wilcoxon handles this, but we log)
    diff = errors1 - errors2
    non_zero_count = np.count_nonzero(diff)
    if non_zero_count < 2:
        logger.warning("Wilcoxon test: insufficient non-zero differences. Result may be unreliable.")
        
    stat, p_val = stats.wilcoxon(errors1, errors2)
    logger.debug(f"Wilcoxon test: W={stat:.4f}, p={p_val:.4f}")
    return float(stat), float(p_val)

def evaluate_model(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Evaluate model performance with multiple metrics.
    
    Args:
        y_true: True values.
        y_pred: Predicted values.
        
    Returns:
        Dictionary of metrics: mse, mae, pearson_r.
    """
    return {
        "mse": calculate_mse(y_true, y_pred),
        "mae": calculate_mae(y_true, y_pred),
        "pearson_r": calculate_pearson_r(y_true, y_pred)
    }

def compare_models(
    y_true: Union[List[float], np.ndarray], 
    y_pred1: Union[List[float], np.ndarray], 
    y_pred2: Union[List[float], np.ndarray]
) -> Dict[str, Any]:
    """
    Compare two models using paired t-test and Wilcoxon test.
    
    This function implements the statistical comparison logic required
    by the project specification, tagging Wilcoxon as PRIMARY and
    t-test as SENSITIVITY.
    
    Args:
        y_true: True values.
        y_pred1: Predictions from model 1.
        y_pred2: Predictions from model 2.
        
    Returns:
        Dictionary with comparison results including:
        - paired_t_test: {t_statistic, p_value} (SENSITIVITY)
        - wilcoxon_test: {statistic, p_value} (PRIMARY)
        - model1_mae, model2_mae
    """
    y_true = np.array(y_true, dtype=float)
    y_pred1 = np.array(y_pred1, dtype=float)
    y_pred2 = np.array(y_pred2, dtype=float)
    
    if not (y_true.shape == y_pred1.shape == y_pred2.shape):
        raise ValueError(f"All input arrays must have the same shape. Got: "
                       f"y_true={y_true.shape}, y_pred1={y_pred1.shape}, y_pred2={y_pred2.shape}")
    
    errors1 = np.abs(y_true - y_pred1)
    errors2 = np.abs(y_true - y_pred2)
    
    # Calculate MAEs for reference
    mae1 = float(np.mean(errors1))
    mae2 = float(np.mean(errors2))
    
    # Perform statistical tests
    t_stat, t_pval = paired_t_test(errors1, errors2)
    w_stat, w_pval = wilcoxon_signed_rank_test(errors1, errors2)
    
    result = {
        "paired_t_test": {
            "t_statistic": t_stat, 
            "p_value": t_pval,
            "test_type": "SENSITIVITY"
        },
        "wilcoxon_test": {
            "statistic": w_stat, 
            "p_value": w_pval,
            "test_type": "PRIMARY"
        },
        "model1_mae": mae1,
        "model2_mae": mae2,
        "model1_better": mae1 < mae2
    }
    
    logger.info(f"Model comparison: Model1 MAE={mae1:.4f}, Model2 MAE={mae2:.4f}, "
               f"Wilcoxon p={w_pval:.4f}, T-test p={t_pval:.4f}")
               
    return result

if __name__ == "__main__":
    # Test with mock data to verify implementation
    y_true = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    y_pred1 = [1.1, 2.1, 2.9, 4.2, 4.8, 6.1, 6.9, 8.1, 8.9, 10.2]
    y_pred2 = [1.2, 2.2, 2.8, 4.1, 4.9, 6.2, 7.0, 8.0, 9.0, 10.1]
    
    print("=== Individual Metrics ===")
    metrics = evaluate_model(y_true, y_pred1)
    print(f"Model 1 Metrics: {metrics}")
    
    print("\n=== Model Comparison ===")
    comparison = compare_models(y_true, y_pred1, y_pred2)
    print(f"Comparison Results: {comparison}")
    
    # Verify test types are correctly tagged
    assert comparison["wilcoxon_test"]["test_type"] == "PRIMARY", "Wilcoxon must be PRIMARY"
    assert comparison["paired_t_test"]["test_type"] == "SENSITIVITY", "T-test must be SENSITIVITY"
    print("\n✓ All assertions passed. Test types correctly tagged.")